import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, desc 
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone 

import functools

# Removed 'mail' from extensions import, as it's not used in this blueprint for sending emails related to events.
from extensions import db 
from models import User, Role, Event, Rating, Category, Registration, Notification, RegistrationStatus 
from forms import CategoryForm, UserRoleForm, NotificationForm 
# Removed 'Message' import, as it's not used in this blueprint for sending emails.
# from flask_mail import Message 

admin_bp = Blueprint('admin', __name__)

# Helper function to check admin role
def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != Role.ADMIN:
            flash('You do not have permission to access the Admin Panel.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Dashboard Route
@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    total_users = db.session.query(func.count(User.id)).scalar()
    total_events = db.session.query(func.count(Event.id)).scalar()
    total_registrations = db.session.query(func.count(Registration.id)).scalar()
    total_categories = db.session.query(func.count(Category.id)).scalar()

    naive_utc_now = datetime.now(timezone.utc).replace(tzinfo=None) 

    recent_users = User.query.order_by(User.id.desc()).limit(4).all()
    
    upcoming_events = Event.query.filter(Event.start_time >= naive_utc_now).order_by(Event.start_time.asc()).limit(3).all()
    
    recent_registrations = Registration.query.order_by(Registration.registration_date.desc()).limit(3).all()

    return render_template('admin/admin_dashboard.html',
                           total_users=total_users,
                           total_events=total_events,
                           total_registrations=total_registrations,
                           total_categories=total_categories,
                           recent_users=recent_users,
                           upcoming_events=upcoming_events,
                           recent_registrations=recent_registrations)

# --- Category Management Routes ---

@admin_bp.route('/manage_categories', methods=['GET', 'POST'])
@admin_required
def manage_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        existing_category = Category.query.filter(func.lower(Category.name) == func.lower(form.name.data)).first()
        if existing_category:
            flash(f'Category "{form.name.data}" already exists.', 'warning')
        else:
            category = Category(name=form.name.data)
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{category.name}" added successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/manage_categories.html', title='Manage Categories', form=form, categories=categories)


@admin_bp.route('/manage_categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        flash('Category not found!', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        if form.name.data != category.name:
            existing_category = Category.query.filter(func.lower(Category.name) == func.lower(form.name.data)).first()
            if existing_category and existing_category.id != category.id:
                flash(f'Category "{form.name.data}" already exists.', 'warning')
                return render_template('admin/edit_category.html', title='Edit Category', form=form, category=category)
        
        category.name = form.name.data
        db.session.commit()
        flash(f'Category "{category.name}" updated successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))
    
    elif request.method == 'GET':
        form.name.data = category.name
        
    return render_template('admin/edit_category.html', title='Edit Category', form=form, category=category)


@admin_bp.route('/manage_categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        flash('Category not found!', 'danger')
        return redirect(url_for('admin.manage_categories'))
    
    if category.events.count() > 0:
        flash(f'Cannot delete category "{category.name}" because it has associated events. Please reassign or delete events first.', 'warning')
        return redirect(url_for('admin.manage_categories'))

    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{category.name}" deleted successfully!', 'success')
    return redirect(url_for('admin.manage_categories'))

# --- User Management Routes ---

@admin_bp.route('/manage_users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users_query = User.query.order_by(User.username.asc())
    users_pagination = users_query.paginate(page=page, per_page=10, error_out=False)

    return render_template('admin/manage_users.html',
                           title='Manage Users',
                           users_pagination=users_pagination)

@admin_bp.route('/manage_users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin.manage_users'))

    form = UserRoleForm(obj=user)
    
    if form.validate_on_submit():
        user.role = Role(form.role.data)
        db.session.commit()
        flash(f'User {user.username} role updated to {user.role.name.title()}!', 'success')
        return redirect(url_for('admin.manage_users'))
    elif request.method == 'GET':
        form.role.data = user.role.value

    return render_template('admin/edit_user.html', title='Edit User', form=form, user=user)

@admin_bp.route('/manage_users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if user == current_user:
        flash("You cannot delete your own account from here!", 'danger')
        return redirect(url_for('admin.manage_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

# --- Registration Management Route ---
@admin_bp.route('/manage_registrations')
@admin_required
def manage_registrations():
    registrations = Registration.query.options(joinedload(Registration.user), joinedload(Registration.event)).order_by(Registration.registration_date.desc()).all()

    return render_template('admin/manage_registrations.html',
                           title='Manage Registrations',
                           registrations=registrations)

# Routes for updating registration statuses - ONLY IN-APP NOTIFICATION
@admin_bp.route('/manage_registrations/<int:reg_id>/approve', methods=['POST'])
@admin_required
def approve_registration(reg_id):
    registration = db.session.get(Registration, reg_id)
    if not registration:
        flash('Registration not found.', 'danger')
        return redirect(url_for('admin.manage_registrations'))
    
    if registration.status == RegistrationStatus.APPROVED:
        flash(f'Registration for {registration.user.username} to {registration.event.title} is already approved.', 'info')
        return redirect(url_for('admin.manage_registrations'))

    registration.status = RegistrationStatus.APPROVED
    db.session.commit()

    # Send in-app notification (REMAINS)
    notification_message = f'Your registration for "{registration.event.title}" has been APPROVED!'
    new_notification = Notification(user_id=registration.user.id, message=notification_message)
    db.session.add(new_notification)
    db.session.commit()

    # Confirmed NO email notification logic here
    flash(f'Registration for {registration.user.username} to {registration.event.title} approved!', 'success') 
    return redirect(url_for('admin.manage_registrations'))

@admin_bp.route('/manage_registrations/<int:reg_id>/reject', methods=['POST'])
@admin_required
def reject_registration(reg_id):
    registration = db.session.get(Registration, reg_id)
    if not registration:
        flash('Registration not found.', 'danger')
        return redirect(url_for('admin.manage_registrations'))
    
    if registration.status == RegistrationStatus.CANCELLED:
        flash(f'Registration for {registration.user.username} to {registration.event.title} is already cancelled/rejected.', 'info')
        return redirect(url_for('admin.manage_registrations'))

    registration.status = RegistrationStatus.CANCELLED 
    db.session.commit()

    # Send in-app notification (REMAINS)
    notification_message = f'Your registration for "{registration.event.title}" has been REJECTED. Please contact the organizer for details.'
    new_notification = Notification(user_id=registration.user.id, message=notification_message)
    db.session.add(new_notification)
    db.session.commit()

    # Confirmed NO email notification logic here
    flash(f'Registration for {registration.user.username} to {registration.event.title} rejected!', 'warning')
    return redirect(url_for('admin.manage_registrations'))

@admin_bp.route('/manage_registrations/<int:reg_id>/cancel', methods=['POST'])
@admin_required
def cancel_registration(reg_id):
    registration = db.session.get(Registration, reg_id)
    if not registration:
        flash('Registration not found.', 'danger')
        return redirect(url_for('admin.manage_registrations'))
    
    if registration.status == RegistrationStatus.CANCELLED:
        flash(f'Registration for {registration.user.username} to {registration.event.title} is already cancelled.', 'info')
        return redirect(url_for('admin.manage_registrations'))

    registration.status = RegistrationStatus.CANCELLED
    db.session.commit()

    # Send in-app notification (REMAINS)
    notification_message = f'Your registration for "{registration.event.title}" has been CANCELLED.'
    new_notification = Notification(user_id=registration.user.id, message=notification_message)
    db.session.add(new_notification)
    db.session.commit()

    # Confirmed NO email notification logic here
    flash(f'Registration for {registration.user.username} to {registration.event.title} cancelled!', 'info')
    return redirect(url_for('admin.manage_registrations'))

# --- Add Notification Sending for Admin Broadcast ---
# This is where the admin can send a general message to all users.
# This does NOT send an email, only an in-app notification, as per your preference.
@admin_bp.route('/send_notification', methods=['GET', 'POST'])
@admin_required
def send_notification():
    form = NotificationForm()
    if form.validate_on_submit():
        message = form.message.data
        
        # Send to all users (basic broadcast) - ONLY IN-APP
        all_users = User.query.all()
        for user in all_users:
            notification = Notification(user_id=user.id, message=message)
            db.session.add(notification)
        db.session.commit()
        flash('Notification sent to all users!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin/send_notification.html', title='Send Notification', form=form)
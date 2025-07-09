import os
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Role, Notification # Corrected import
from forms import RegistrationForm, LoginForm, UpdateAccountForm, ChangePasswordForm, RequestResetForm, ResetPasswordForm # Ensure all forms are imported
from utils import save_profile_picture # Corrected import

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            role=Role(form.role.data)
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile/<string:username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = None
    if user == current_user:
        form = UpdateAccountForm(original_username=current_user.username, original_email=current_user.email)
        if form.validate_on_submit():
            if form.profile_picture.data:
                current_user.profile_picture = save_profile_picture(form.profile_picture.data)
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('auth.profile', username=current_user.username))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
    
    profile_image = url_for('static', filename=user.profile_picture)
    
    print(f"--- DEBUG: URL being sent to template is: {profile_image} ---")
    print(f"--- DEBUG: Form object (None if not current user's profile): {form} ---")
    
    return render_template('auth/profile.html', title=f"{user.username}'s Profile", form=form, user=user, image_file=profile_image)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been changed successfully!', 'success')
            return redirect(url_for('auth.profile', username=current_user.username))
        else:
            flash('Incorrect old password.', 'danger')
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RequestResetForm()
    # Logic for sending reset email would go here (e.g., using Flask-Mail)
    if form.validate_on_submit():
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    # Logic for token validation and actual password reset
    # User = User.verify_reset_token(token) # Example method to verify token
    # if user is None:
    #    flash('That is an invalid or expired token.', 'warning')
    #    return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # user.set_password(form.password.data)
        # db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_token.html', title='Reset Password', form=form)

@auth_bp.route('/follow/<string:username>', methods=['POST'])
@login_required
def follow_user(username):
    user_to_follow = User.query.filter_by(username=username).first_or_404()
    if user_to_follow == current_user:
        flash('You cannot follow yourself.', 'warning')
        return redirect(url_for('auth.profile', username=username))
    if current_user.follow(user_to_follow): # Call the follow method on the User model
        db.session.commit()
        flash(f'You are now following {username}!', 'success')
    else:
        flash(f'You are already following {username}.', 'info')
    return redirect(url_for('auth.profile', username=username))

@auth_bp.route('/unfollow/<string:username>', methods=['POST'])
@login_required
def unfollow_user(username):
    user_to_unfollow = User.query.filter_by(username=username).first_or_404()
    if user_to_unfollow == current_user:
        flash('You cannot unfollow yourself.', 'warning')
        return redirect(url_for('auth.profile', username=username))
    if current_user.unfollow(user_to_unfollow): # Call the unfollow method on the User model
        db.session.commit()
        flash(f'You have unfollowed {username}.', 'success')
    else:
        flash(f'You are not following {username}.', 'info')
    return redirect(url_for('auth.profile', username=username))

@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user # The user requesting deletion
    
    # Optional: Re-authenticate for sensitive action, e.g., prompt for password again
    # if not user.check_password(request.form.get('password_confirm')):
    #     flash('Incorrect password. Account not deleted.', 'danger')
    #     return redirect(url_for('auth.profile', username=user.username))

    logout_user() # Log out the user immediately
    db.session.delete(user)
    db.session.commit()
    flash('Your account has been deleted permanently.', 'info')
    return redirect(url_for('auth.register')) # Redirect to registration or homepage

@auth_bp.route('/notifications')
@login_required
def view_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    
    # Mark all unread notifications as read when the user views them
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notif in unread_notifications:
        notif.is_read = True
    db.session.commit()

    return render_template('auth/notifications.html', title='Your Notifications', notifications=notifications)
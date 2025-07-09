my-projects

The Campus Event Management Platform is a web application designed to streamline the process of organizing, discovering, and participating in various campus events. It aims to transform event management into a modern, responsive, and intuitive experience. Core Features and Modules: 

-User Management: The system supports three user roles: Administrator, Club Organizer, and Regular Student. It includes functionalities for user registration, login, password changes, and managing personal profiles. Users can edit their profiles, including updating their username, email, and profile picture, and can also follow other users like event organizers. 

-Event Management: Organizers and administrators can create, edit, and delete events, specifying details such as time, location, and event posters. Events can be categorized and searched for by users. The platform provides an event dashboard displaying upcoming events and a dedicated event details page for comprehensive information. 

-Registration & Check-in: The platform facilitates online registration for events. It also includes features for QR code generation and validation for attendance tracking, and the ability to export participant lists in Excel format. 

-Data Visualization: Users can view an interactive event calendar. The system also includes basic data statistics, such as participation statistics. A simple event rating system allows registered attendees to rate events and leave comments. 

-Administrative & Organizational Tools: Dedicated dashboards are provided for organizers and administrators. Organizers have an overview of their events and registrations , while administrators have comprehensive tools to manage users, events, categories, and registrations across the entire system. Technical Stack: 

-The application is built using: 

-Backend: Flask (Python) with SQLite as the database. SQLAlchemy is used as the Object-Relational Mapper (ORM). 

-Frontend: HTML5, CSS3, JavaScript. Tailwind CSS is used as a utility-first CSS framework for UI development and responsive design. Alpine.js is used for interactive JavaScript behavior , and Font Awesome provides icons. 

-Other Key Technologies: Flask-WTF and WTForms for form handling , Flask-Login for user authentication , Flask-Migrate for database migrations , and Python's 

-datetime module for date/time handling.

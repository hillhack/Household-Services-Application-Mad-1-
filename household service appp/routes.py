from flask import Blueprint, render_template, request, redirect, url_for, flash, session,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Customer, Professional, ServiceRequest, Service, db
from datetime import datetime
import io
from sqlalchemy import func
main = Blueprint('main', __name__)

def get_user(user_id):
    return User.query.get_or_404(user_id)

@main.route('/')
def index():
    return render_template('index.html')

# Home/Login route
@main.route('/home')
def home():
    return render_template('login.html')

# Login route
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role  # Store user's role in session

            # Redirect based on user role
            if user.role == 'customer':
                customer = Customer.query.filter_by(user_id=user.id).first()
                if customer and  customer.block== "NO":
                    return redirect(url_for('main.customer_dash', customer_id=customer.id))
                else:
                    flash('You have been blocked', category='error')
                
            elif user.role == 'professional':
                professional = Professional.query.filter_by(user_id=user.id).first()
                if professional and professional.block == "NO":
                    return redirect(url_for('main.professional_dash', professional_id=professional.id))
                else:
                    flash('You have been blocked', category='error')
                
            elif user.role == 'admin':
                return redirect(url_for('main.admin_dash', user_id=user.id))
        else:
            flash('Invalid email or password.', category='error')
    return render_template('login.html')

# Register route
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        username = request.form.get('username')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash("Email already exists.", category="error")
        elif len(email) < 4:
            flash("Email must be greater than 3 characters.", category="error")
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
        elif len(password1) < 5:
            flash("Password must be at least 5 characters.", category="error")
        else:
            hashed_password = generate_password_hash(password1, method='pbkdf2:sha256')
            new_user = User(email=email, password=hashed_password, username=username, role=role)
            db.session.add(new_user)
            db.session.commit()

            # Create customer or professional profile
            if role == 'customer':
                new_customer = Customer(user_id=new_user.id)
                db.session.add(new_customer)
            elif role == 'professional':
                new_professional = Professional(user_id=new_user.id)
                db.session.add(new_professional)

            db.session.commit()
            flash('Registration successful! Please login.', category='success')
            return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/admin_dash')
def admin_dash():
    customers = Customer.query.all()
    professionals = Professional.query.all()
    services = Service.query.with_entities(Service.name,Service.base_price,Service.id).distinct().all()
    return render_template('admin_dash.html', customers=customers, professionals=professionals,services=services)

# Customer dashboard route
@main.route('/customer_dash/<int:customer_id>')
def customer_dash(customer_id):
    customer = Customer.query.get(customer_id)
    user = User.query.get(customer.user_id)
    service_requests = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    services = Service.query.with_entities(Service.name).all()

    pending_requests = ServiceRequest.query.filter_by(customer_id=customer_id, service_status='Pending').all()

    historical_requests = ServiceRequest.query.filter(
        ServiceRequest.customer_id == customer_id,
        ServiceRequest.service_status.in_(['Accepted', 'Rejected'])
    ).all()

    return render_template('customer_dash.html', user=user, services=services, pending_requests=pending_requests, 
                           service_requests=service_requests, customer_id=customer.id, historical_requests=historical_requests)

# Professional dashboard route
@main.route('/professional_dash/<int:professional_id>')
def professional_dash(professional_id):
    professional = Professional.query.get(professional_id)
    service_requests = ServiceRequest.query.filter_by(professional_id=professional.id).all()
    user = User.query.get(professional.user_id)
    services = Service.query.filter_by(professional_id=professional.id).all()

    return render_template('professional_dash.html', user=user, professional=professional, services=services,
                           service_requests=service_requests)



# Add service route
@main.route('/add_service/<int:professional_id>', methods=['GET', 'POST'])
def add_service(professional_id):
    professional = Professional.query.get_or_404(professional_id)
    if not professional or professional.approved_status != 'Approved':
        flash('Your profile is not mainroved yet. Please wait for admin mainroval to add services.', category='error')
        return redirect(url_for('main.professional_dash', professional_id=professional.id))

    if request.method == 'POST':
        name = request.form.get('name')
        base_price= ('Not Set')
        experience = request.form.get('experience')
        description = request.form.get('description')

        new_service = Service(name=name,base_price=base_price,  experience=experience, description=description, professional_id=professional_id)
        db.session.add(new_service)
        db.session.commit()

        flash('Service added successfully!', category='success')
        return redirect(url_for('main.professional_dash', professional_id=professional_id))

# Edit profile route
@main.route('/edit_profile/<int:user_id>/<string:user_type>', methods=['GET', 'POST'])
def edit_profile(user_id, user_type):
    if user_type == 'customer':
        profile = Customer.query.filter_by(id=user_id).first()
    elif user_type == 'professional':
        profile = Professional.query.filter_by(id=user_id).first()
    else:
        flash('Invalid user type!', category='error')
        return redirect(url_for('main.index'))  # Redirect to the homepage for invalid user types

    if not profile:
        flash('Profile not found!', category='error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Fetch form data
        name = request.form.get('name')
        contact_no = request.form.get('contact_no')
        address = request.form.get('address')

        # Update profile fields
        profile.name = name
        profile.contact_no = contact_no
        profile.address = address

        # Save changes to the database
        db.session.commit()
        flash('Profile updated successfully!', category='success')

        # Redirect to the appropriate dashboard based on user type
        if user_type == 'customer':
            return redirect(url_for('main.customer_dash', customer_id=profile.id))
        elif user_type == 'professional':
            return redirect(url_for('main.professional_dash', professional_id=profile.id))

    # Render the edit profile template
    return render_template(
        'edit_profile.html',
        user_id=user_id,
        user_type=user_type,
        profile=profile
    )


# Delete service route
@main.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    professional = service.professional

    try:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully!', category='success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", category='error')
    return redirect(url_for('main.professional_dash', professional_id=professional.id))

@main.route('/professionals')
def professionals():
    service_name = request.args.get('service_name')
    customer_id = request.args.get('customer_id')
    service = Service.query.filter_by(name=service_name).first()
    # Query professionals offering the specific service
    professionals = db.session.query(
        Professional.id, Professional.name, Professional.contact_no,
        Service.base_price, Service.experience, Service.description
    ).join(Service, Professional.id == Service.professional_id) \
        .filter(Service.name.ilike(f'%{service_name}%')) \
        .all()

    if not professionals:
        flash(f'No professionals found for the service "{service_name}"', category='warning')

    return render_template('professionals.html', professionals=professionals, customer_id=customer_id,service=service)
@main.route('/update_service/<int:service_id>', methods=['GET', 'POST'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    professional = Professional.query.get(service.professional_id)

    if request.method == 'POST':
        service.name = request.form.get('name')
        service.price = request.form.get('price')
        service.experience = request.form.get('experience')
        service.description = request.form.get('description')

        try:
            db.session.commit()
            flash('Service updated successfully!', category='success')
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", category='error')

        return redirect(url_for('main.professional_dash', professional_id=professional.id))

    return render_template('update_service.html', service=service)
@main.route('/handle-request/<int:request_id>', methods=['POST'])
def handle_request(request_id):
    action = request.form.get('action')  # "accept" or "reject"
    service_request = ServiceRequest.query.get(request_id)

    if service_request.service_status == 'Pending':
        if action == 'accept':
            service_request.service_status = 'Accepted'
            flash('Service request accepted.', category='success')
        elif action == 'reject':
            service_request.service_status = 'Rejected'
            flash('Service request rejected.', category='error')

        db.session.commit()
    else:
        flash('Service request already processed.', category='info')

    return redirect(url_for('main.professional_dash', professional_id=service_request.professional_id))
@main.route('/send-request', methods=['POST'])
def send_request():
    professional_name = request.form.get('professional_name')
    professional_id = request.form.get('professional_id')
    customer_id = request.form.get('customer_id')
    service_id = request.form.get('service_id')
    due_date_str = request.form.get('due_date')
    date_of_completion = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

    new_request = ServiceRequest(
        service_id=service_id,
        customer_id=customer_id,
        professional_id=professional_id,
        date_of_request=datetime.utcnow(),
        date_of_completion =date_of_completion ,
        service_status='Pending'  # Initial status of the request
    )

    db.session.add(new_request)
    db.session.commit()

    flash('Your request has been sent to the professional!', category='success')
    return redirect(url_for('main.customer_dash', customer_id=customer_id))

@main.route('/cancel_request/<int:request_id>', methods=['POST'])
def cancel_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if service_request.service_status == 'Pending':
        try:
            db.session.delete(service_request)
            db.session.commit()
            flash('Service request canceled successfully.', category='success')
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while canceling the request: {str(e)}", category='error')
    else:
        flash('Request cannot be canceled or does not exist.', category='error')
    return redirect(url_for('main.customer_dash', customer_id=service_request.customer_id))

@main.route('/manage_professionals', methods=['GET'])
def manage_professionals():
    
    professionals = Professional.query.all()

    return render_template('manage_professionals.html', professionals=professionals)


@main.route('/approve_professional/<int:professional_id>', methods=['POST'])
def approve_professional(professional_id):
    # Fetch the professional from the database
    professional = Professional.query.get_or_404(professional_id)

    if professional.approved_status == 'Pending':
        # Update the approved status
        professional.approved_status = 'Approved'
        db.session.commit()
        flash(f"Professional ID {professional_id} has been approved.", "success")
    else:
        flash("This professional is already approved.", "warning")
    
    # Redirect back to the admin dashboard or relevant page
    return redirect(url_for('main.admin_dash'))

@main.route('/complete_work/<int:professional_id>', methods=['POST'])
def complete_work(professional_id):
    request_id = request.form.get('request_id')

    service_request = ServiceRequest.query.get(request_id)
    
    if service_request:
        service_request.service_status = 'Completed'
        db.session.commit()
        flash('Work status updated to Completed.', 'success')

    # Redirect back to the current work page
    return redirect(url_for('main.professional_dash',professional_id=professional_id))  # Adjust this to your current page route

@main.route('/summary/<string:user_type>/<int:user_id>')
def summary(user_type, user_id):
    # Fetch the user and service requests based on the user_type
    if user_type == 'customer':
        user = Customer.query.get_or_404(user_id)
        service_requests = ServiceRequest.query.filter_by(customer_id=user.id).all()
    elif user_type == 'professional':
        user = Professional.query.get_or_404(user_id)
        service_requests = ServiceRequest.query.filter_by(professional_id=user.id).all()
    else:
        return "Invalid user type", 400  # Return an error if user_type is not recognized

    # Calculate request summaries
    completed_requests = sum(1 for r in service_requests if r.service_status == 'Completed')
    pending_requests = sum(1 for r in service_requests if r.service_status == 'Pending')
    accepted_requests = sum(1 for r in service_requests if r.service_status == 'Accepted')

    # Prepare data for the template
    request_data = {
        "completed_requests": completed_requests,
        "pending_requests": pending_requests,
        "accepted_requests": accepted_requests
    }

    # Ensure request_data is passed to the template
    return render_template('graph.html', request_data=request_data, user=user, user_type=user_type)

@main.route('/rate_review/<int:request_id>', methods=['GET','POST'])
def rate_and_review(request_id):
    # Fetch the service request by ID
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    # Ensure the service is completed before allowing rating/review
    if service_request.service_status != 'Completed':
        flash("You can only rate and review completed services.", "warning")
        return redirect(url_for('customer_dashboard'))  # Replace with your actual dashboard route

    if request.method == 'POST':
        # Get the rating and review from the form submission
        rating = request.form.get('rating')
        review = request.form.get('review')
        service_request.rating = int(rating)

        service_request.review = review.strip() if review else None
        db.session.commit()
        flash("Thank you for your feedback!", "success")

    return render_template('rate_review.html', request_id=request_id)

@main.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        flash("Service not found!", "danger")
        return redirect(url_for('main.admin_dashboard'))

    if request.method == 'POST':
        service.name = request.form['service_name']
        service.base_price = request.form['base_price']
        db.session.commit()
        flash(f"Service '{service.name}' updated successfully.", "success")
        return redirect(url_for('main.admin_dash'))

    return render_template('edit_service.html', service=service)

@main.route('/admin/block_user/<string:user_type>/<int:user_id>', methods=['POST'])
def block_user(user_type, user_id):
    if user_type == 'customer':
        customer = Customer.query.get(user_id)
        if customer:
            customer.block = "YES" if customer.block == "NO" else "NO"
            db.session.commit()
            flash(f"Customer {'blocked' if customer.block == 'YES' else 'unblocked'} successfully.", 'success')
        else:
            flash("Customer not found.", 'danger')
    elif user_type == 'professional':
        professional = Professional.query.get(user_id)
        if professional:
            professional.block = "YES" if professional.block == "NO" else "NO"
            db.session.commit()
            flash(f"Professional {'blocked' if professional.block == 'YES' else 'unblocked'} successfully.", 'success')
        else:
            flash("Professional not found.", 'danger')
    else:
        flash("Invalid user type.", 'danger')
    
    return redirect(url_for('main.admin_dash'))



@main.route('/logout')
def logout():
    session.clear()
    flash('You have logged out successfully!', category='success')
    return redirect(url_for('main.home'))

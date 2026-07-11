from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from services.auth import ROLES, authenticate, create_user, delete_user, list_audit, list_users, role_required, update_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = authenticate(request.form.get('username', ''), request.form.get('password', ''))
        if not user:
            flash('Invalid username or password.', 'error')
            return render_template('login.html'), 401
        session.clear(); session['user_id'] = user['id']
        next_url = request.args.get('next') or request.form.get('next') or '/'
        if not next_url.startswith('/'):
            next_url = '/'
        return redirect(next_url)
    return render_template('login.html', next=request.args.get('next', ''))

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/users')
@role_required('admin')
def users_page():
    return render_template('users.html', active='users', users=list_users(), roles=ROLES)

@auth_bp.route('/users/create', methods=['POST'])
@role_required('admin')
def create_user_route():
    try:
        create_user(request.form.get('username'), request.form.get('password'), request.form.get('role', 'viewer'), request.form.get('display_name'))
        flash('User created.', 'success')
    except Exception as exc:
        flash(str(exc), 'error')
    return redirect(url_for('auth.users_page'))

@auth_bp.route('/users/<int:user_id>/update', methods=['POST'])
@role_required('admin')
def update_user_route(user_id):
    try:
        update_user(user_id, display_name=request.form.get('display_name'), role=request.form.get('role'),
                    enabled=request.form.get('enabled') == '1', password=request.form.get('password') or None)
        flash('User updated.', 'success')
    except Exception as exc:
        flash(str(exc), 'error')
    return redirect(url_for('auth.users_page'))

@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user_route(user_id):
    if session.get('user_id') == user_id:
        flash('You cannot delete your own account.', 'error')
    else:
        delete_user(user_id); flash('User deleted.', 'success')
    return redirect(url_for('auth.users_page'))

@auth_bp.route('/audit')
@role_required('admin')
def audit_page():
    return render_template('audit.html', active='audit', entries=list_audit())

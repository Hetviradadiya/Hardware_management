// Settings Page JavaScript
let currentUserId = null;
let currentRoleId = null;
let currentUserData = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize settings page
    loadCurrentUser();
    loadUsers();
    loadRoles();
    
    // Event listeners
    document.getElementById('addUserBtn').addEventListener('click', showAddUserModal);
    document.getElementById('addRoleBtn').addEventListener('click', showAddRoleModal);
    document.getElementById('saveUserBtn').addEventListener('click', saveUser);
    document.getElementById('saveRoleBtn').addEventListener('click', saveRole);
    document.getElementById('userSearch').addEventListener('input', searchUsers);
    
    // Form submissions
    document.getElementById('profileForm').addEventListener('submit', updateProfile);
    document.getElementById('changePasswordForm').addEventListener('submit', changePassword);
});

// Load current user data
function loadCurrentUser() {
    fetch('/admin_api/users/current_user/', {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        currentUserData = data;
        populateProfileForm(data);
    })
    .catch(error => {
        console.error('Error loading current user:', error);
        showToast('Error', 'Failed to load user profile', 'danger');
    });
}

// Load users list
function loadUsers(page = 1, search = '') {
    let url = `/admin_api/users/?page=${page}`;
    if (search) {
        url += `&search=${encodeURIComponent(search)}`;
    }
    
    fetch(url, {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        populateUsersTable(data.results || data);
        updatePagination('usersPagination', data, page, loadUsers);
    })
    .catch(error => {
        console.error('Error loading users:', error);
        showToast('Error', 'Failed to load users', 'danger');
    });
}

// Load roles list
function loadRoles() {
    fetch('/admin_api/roles/', {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        populateRolesTable(data.results || data);
        populateRoleDropdown(data.results || data);
    })
    .catch(error => {
        console.error('Error loading roles:', error);
        showToast('Error', 'Failed to load roles', 'danger');
    });
}

// Populate users table
function populateUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar avatar-sm me-2">
                        <div class="avatar-initial bg-label-primary rounded-circle">
                            ${user.full_name.charAt(0).toUpperCase()}
                        </div>
                    </div>
                    <div>
                        <strong>${user.full_name}</strong>
                        ${user.username ? `<br><small class="text-muted">@${user.username}</small>` : ''}
                    </div>
                </div>
            </td>
            <td>${user.email}</td>
            <td>${user.mobile}</td>
            <td>
                ${user.role_name ? `<span class="badge bg-info">${user.role_name}</span>` : '<span class="text-muted">No Role</span>'}
            </td>
            <td>
                <span class="badge bg-${user.is_active ? 'success' : 'danger'}">
                    ${user.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>
                <small class="text-muted">${formatDate(user.date_joined)}</small>
            </td>
            <td>
                <div class="dropdown">
                    <button class="btn btn-sm btn-outline-primary dropdown-toggle" data-bs-toggle="dropdown">
                        Actions
                    </button>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="#" onclick="editUser(${user.id})">
                            <i class="bx bx-edit me-1"></i>Edit
                        </a></li>
                        <li><a class="dropdown-item" href="#" onclick="changeUserPassword(${user.id})">
                            <i class="bx bx-key me-1"></i>Change Password
                        </a></li>
                        <li><a class="dropdown-item" href="#" onclick="toggleUserStatus(${user.id})">
                            <i class="bx bx-${user.is_active ? 'x' : 'check'} me-1"></i>
                            ${user.is_active ? 'Deactivate' : 'Activate'}
                        </a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" onclick="deleteUser(${user.id})">
                            <i class="bx bx-trash me-1"></i>Delete
                        </a></li>
                    </ul>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Populate roles table
function populateRolesTable(roles) {
    const tbody = document.getElementById('rolesTableBody');
    tbody.innerHTML = '';
    
    roles.forEach(role => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${role.name}</strong></td>
            <td>${role.description || '<span class="text-muted">No description</span>'}</td>
            <td><small class="text-muted">${formatDate(role.created_at)}</small></td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editRole(${role.id})">
                    <i class="bx bx-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteRole(${role.id})">
                    <i class="bx bx-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Populate role dropdown
function populateRoleDropdown(roles) {
    const select = document.getElementById('userRole');
    select.innerHTML = '<option value="">Select Role</option>';
    
    roles.forEach(role => {
        const option = document.createElement('option');
        option.value = role.id;
        option.textContent = role.name;
        select.appendChild(option);
    });
}

// Show add user modal
function showAddUserModal() {
    currentUserId = null;
    document.getElementById('userModalTitle').textContent = 'Add User';
    document.getElementById('passwordSection').style.display = 'block';
    document.getElementById('userForm').reset();
    document.getElementById('userIsActive').checked = true;
    new bootstrap.Modal(document.getElementById('userModal')).show();
}

// Show add role modal
function showAddRoleModal() {
    currentRoleId = null;
    document.getElementById('roleModalTitle').textContent = 'Add Role';
    document.getElementById('roleForm').reset();
    new bootstrap.Modal(document.getElementById('roleModal')).show();
}

// Edit user
function editUser(userId) {
    fetch(`/admin_api/users/${userId}/`, {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(user => {
        currentUserId = userId;
        document.getElementById('userModalTitle').textContent = 'Edit User';
        document.getElementById('passwordSection').style.display = 'none';
        
        // Populate form
        document.getElementById('userFullName').value = user.full_name;
        document.getElementById('userUsername').value = user.username || '';
        document.getElementById('userEmail').value = user.email;
        document.getElementById('userMobile').value = user.mobile;
        document.getElementById('userRole').value = user.role || '';
        document.getElementById('userIsActive').checked = user.is_active;
        document.getElementById('userIsStaff').checked = user.is_staff;
        document.getElementById('userAddress').value = user.address_line || '';
        document.getElementById('userCity').value = user.city || '';
        document.getElementById('userState').value = user.state || '';
        document.getElementById('userPostal').value = user.postal_code || '';
        
        new bootstrap.Modal(document.getElementById('userModal')).show();
    })
    .catch(error => {
        console.error('Error loading user:', error);
        showToast('Error', 'Failed to load user data', 'danger');
    });
}

// Edit role
function editRole(roleId) {
    fetch(`/admin_api/roles/${roleId}/`, {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(role => {
        currentRoleId = roleId;
        document.getElementById('roleModalTitle').textContent = 'Edit Role';
        document.getElementById('roleName').value = role.name;
        document.getElementById('roleDescription').value = role.description || '';
        
        new bootstrap.Modal(document.getElementById('roleModal')).show();
    })
    .catch(error => {
        console.error('Error loading role:', error);
        showToast('Error', 'Failed to load role data', 'danger');
    });
}

// Save user
function saveUser() {
    const formData = {
        full_name: document.getElementById('userFullName').value,
        username: document.getElementById('userUsername').value,
        email: document.getElementById('userEmail').value,
        mobile: document.getElementById('userMobile').value,
        role: document.getElementById('userRole').value || null,
        is_active: document.getElementById('userIsActive').checked,
        is_staff: document.getElementById('userIsStaff').checked,
        address_line: document.getElementById('userAddress').value,
        city: document.getElementById('userCity').value,
        state: document.getElementById('userState').value,
        postal_code: document.getElementById('userPostal').value
    };
    
    // Add password fields for new users
    if (!currentUserId) {
        formData.password = document.getElementById('userPassword').value;
        formData.confirm_password = document.getElementById('userConfirmPassword').value;
    }
    
    const url = currentUserId ? `/admin_api/users/${currentUserId}/` : '/admin_api/users/';
    const method = currentUserId ? 'PATCH' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error || data.errors) {
            throw new Error(data.error || 'Validation errors occurred');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
        loadUsers();
        showToast('Success', `User ${currentUserId ? 'updated' : 'created'} successfully`, 'success');
    })
    .catch(error => {
        console.error('Error saving user:', error);
        showToast('Error', error.message || 'Failed to save user', 'danger');
    });
}

// Save role
function saveRole() {
    const formData = {
        name: document.getElementById('roleName').value,
        description: document.getElementById('roleDescription').value
    };
    
    const url = currentRoleId ? `/admin_api/roles/${currentRoleId}/` : '/admin_api/roles/';
    const method = currentRoleId ? 'PATCH' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        bootstrap.Modal.getInstance(document.getElementById('roleModal')).hide();
        loadRoles();
        showToast('Success', `Role ${currentRoleId ? 'updated' : 'created'} successfully`, 'success');
    })
    .catch(error => {
        console.error('Error saving role:', error);
        showToast('Error', error.message || 'Failed to save role', 'danger');
    });
}

// Toggle user status
function toggleUserStatus(userId) {
    fetch(`/admin_api/users/${userId}/toggle_status/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        loadUsers();
        showToast('Success', 'User status updated successfully', 'success');
    })
    .catch(error => {
        console.error('Error toggling user status:', error);
        showToast('Error', error.message || 'Failed to update user status', 'danger');
    });
}

// Delete user
function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        fetch(`/admin_api/users/${userId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (response.ok) {
                loadUsers();
                showToast('Success', 'User deleted successfully', 'success');
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to delete user');
                });
            }
        })
        .catch(error => {
            console.error('Error deleting user:', error);
            showToast('Error', error.message, 'danger');
        });
    }
}

// Delete role
function deleteRole(roleId) {
    if (confirm('Are you sure you want to delete this role? This action cannot be undone.')) {
        fetch(`/admin_api/roles/${roleId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            if (response.ok) {
                loadRoles();
                showToast('Success', 'Role deleted successfully', 'success');
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to delete role');
                });
            }
        })
        .catch(error => {
            console.error('Error deleting role:', error);
            showToast('Error', error.message, 'danger');
        });
    }
}

// Search users
function searchUsers() {
    const searchTerm = document.getElementById('userSearch').value;
    loadUsers(1, searchTerm);
}

// Populate profile form
function populateProfileForm(user) {
    document.getElementById('profileFullName').value = user.full_name;
    document.getElementById('profileUsername').value = user.username || '';
    document.getElementById('profileEmail').value = user.email;
    document.getElementById('profileMobile').value = user.mobile;
    document.getElementById('profileAddress').value = user.address_line || '';
    document.getElementById('profileCity').value = user.city || '';
    document.getElementById('profileState').value = user.state || '';
    document.getElementById('profilePostal').value = user.postal_code || '';
}

// Update profile
function updateProfile(e) {
    e.preventDefault();
    
    const formData = {
        full_name: document.getElementById('profileFullName').value,
        username: document.getElementById('profileUsername').value,
        email: document.getElementById('profileEmail').value,
        mobile: document.getElementById('profileMobile').value,
        address_line: document.getElementById('profileAddress').value,
        city: document.getElementById('profileCity').value,
        state: document.getElementById('profileState').value,
        postal_code: document.getElementById('profilePostal').value
    };
    
    fetch(`/admin_api/users/${currentUserData.id}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        currentUserData = data;
        showToast('Success', 'Profile updated successfully', 'success');
    })
    .catch(error => {
        console.error('Error updating profile:', error);
        showToast('Error', error.message || 'Failed to update profile', 'danger');
    });
}

// Change password
function changePassword(e) {
    e.preventDefault();
    
    const formData = {
        old_password: document.getElementById('currentPassword').value,
        new_password: document.getElementById('newPassword').value,
        confirm_password: document.getElementById('confirmPassword').value
    };
    
    fetch(`/admin_api/users/${currentUserData.id}/change_password/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        document.getElementById('changePasswordForm').reset();
        showToast('Success', 'Password changed successfully', 'success');
    })
    .catch(error => {
        console.error('Error changing password:', error);
        showToast('Error', error.message || 'Failed to change password', 'danger');
    });
}

// Utility functions
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

function updatePagination(containerId, data, currentPage, loadFunction) {
    const container = document.getElementById(containerId);
    if (!data.total_pages || data.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHtml = '<ul class="pagination">';
    
    // Previous button
    if (data.current_page > 1) {
        paginationHtml += `<li class="page-item">
            <a class="page-link" href="#" onclick="${loadFunction.name}(${currentPage - 1})">Previous</a>
        </li>`;
    }
    
    // Page numbers
    for (let i = 1; i <= data.total_pages; i++) {
        paginationHtml += `<li class="page-item ${i === data.current_page ? 'active' : ''}">
            <a class="page-link" href="#" onclick="${loadFunction.name}(${i})">${i}</a>
        </li>`;
    }
    
    // Next button
    if (data.current_page < data.total_pages) {
        paginationHtml += `<li class="page-item">
            <a class="page-link" href="#" onclick="${loadFunction.name}(${currentPage + 1})">Next</a>
        </li>`;
    }
    
    paginationHtml += '</ul>';
    container.innerHTML = paginationHtml;
}

// Note: showToast function is now available globally from layout
// Removed local showToast function to use the global one

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
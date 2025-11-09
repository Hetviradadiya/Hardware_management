from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from ..models import UserAccount, Role
from ..serializers import UserProfileSerializer, UserCreateSerializer, RoleSerializer
from inventory_app.pagination import ListPagination


class UserManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users in settings"""
    permission_classes = [IsAuthenticated]
    pagination_class = ListPagination
    queryset = UserAccount.objects.all().order_by('-date_joined')
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email', 'mobile', 'username']
    
    def get_serializer_class(self):
        """Return different serializer based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserProfileSerializer
    
    def get_queryset(self):
        """Filter users based on permissions"""
        queryset = UserAccount.objects.all().order_by('-date_joined')
        
        # If not superuser, only show users created by current user
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create new user"""
        data = request.data.copy()
        data['created_by'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.created_by = request.user
            user.save()
            
            # Return user data with profile serializer
            profile_serializer = UserProfileSerializer(user)
            return Response(profile_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update user profile"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check permissions - users can only edit themselves unless superuser
        if not request.user.is_superuser and instance != request.user:
            return Response(
                {"error": "You can only edit your own profile"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user (only superuser can delete)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superuser can delete users"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        
        # Prevent deleting self
        if instance == request.user:
            return Response(
                {"error": "You cannot delete your own account"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password"""
        user = self.get_object()
        
        # Check permissions
        if not request.user.is_superuser and user != request.user:
            return Response(
                {"error": "You can only change your own password"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # For admin changing other user's password, old password is not required
        is_admin_changing_other_user = request.user.is_superuser and user != request.user
        
        if is_admin_changing_other_user:
            # Admin changing another user's password - only new password fields required
            errors = {}
            if not new_password:
                errors["new_password"] = ["This field is required."]
            if not confirm_password:
                errors["confirm_password"] = ["This field is required."]
            
            if errors:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            # User changing their own password - all fields required
            errors = {}
            if not old_password:
                errors["old_password"] = ["This field is required."]
            if not new_password:
                errors["new_password"] = ["This field is required."]
            if not confirm_password:
                errors["confirm_password"] = ["This field is required."]
            
            if errors:
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate old password (only for own account)
            if not check_password(old_password, user.password):
                return Response(
                    {"old_password": ["Current password is incorrect."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate password match
        if new_password != confirm_password:
            return Response(
                {"confirm_password": ["New passwords do not match."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password length
        if len(new_password) < 8:
            return Response(
                {"new_password": ["Password must be at least 8 characters long."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Update session if changing own password
        if user == request.user:
            update_session_auth_hash(request, user)
        
        return Response({"success": "Password changed successfully"})
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle user active status (superuser only)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superuser can change user status"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Prevent deactivating self
        if user == request.user:
            return Response(
                {"error": "You cannot deactivate your own account"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = not user.is_active
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current_user(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RoleManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing roles"""
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all().order_by('name')
    serializer_class = RoleSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new role (superuser only)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superuser can create roles"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update role (superuser only)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superuser can update roles"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete role (superuser only)"""
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superuser can delete roles"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        role = self.get_object()
        
        # Check if role is in use
        if UserAccount.objects.filter(role=role).exists():
            return Response(
                {"error": "Cannot delete role that is assigned to users"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
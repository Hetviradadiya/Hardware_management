from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.urls import reverse
from django.conf import settings
import os

# REST Framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to dashboards/urls.py file for more pages.
"""

class DashboardsView(TemplateView):
    # def dispatch(self, request, *args, **kwargs):
    #     # Always allow access if user is logged in
    #     return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        template = self.template_name
        breadcrumbs = [{"label": "Home", "url": reverse("index")}]

        def section(label, url=None):
            breadcrumbs.append({"label": label, "url": url} if url else {"label": label})

        route_map = {
            # "user_list.html": ("users", None),
            # "user_add.html": ("Users", reverse("users"), "Add User"),
            # "user_edit.html": ("Users", reverse("users"), "Edit User"),

            # "properties_list.html": ("Properties", None),
            # "property_detail.html": ("Properties", reverse("properties"), "Property Detail"),
            # "property_add.html": ("Properties", reverse("properties"), "Add Property"),
            # "property_edit.html": ("Properties", reverse("properties"), "Edit Property"),

            # "Projects_list.html": ("Projects", None),
            # "Projects_add.html": ("Projects", reverse("get-projects"), "Add Project"),
            # "Projects_edit.html": ("Projects", reverse("get-projects"), "Edit Project"),

            # "property_types_list.html": ("Property Types", None),
            # "property_type_add.html": ("Property Types", reverse("property_type"), "Add Property Type"),
            # "property_type_edit.html": ("Property Types", reverse("property_type"), "Edit Property Type"),

            # "Locations_list.html": ("Locations", None),
            # "Locations_add.html": ("Locations", reverse("get-locations"), "Add Location"),
            # "Locations_edit.html": ("Locations", reverse("get-locations"), "Edit Location"),

            # "leads_list.html": ("Leads", None),
            # "leads_detail.html": ("Leads", reverse("leads"), "Lead Detail"),
            # "lead_add.html": ("Leads", reverse("leads"), "Add Lead"),
            # "lead_edit.html": ("Leads", reverse("leads"), "Leads Detail", "DYNAMIC", "Edit Lead"),
            # "leadFollowUp_list.html": ("Leads", reverse("leads"), "Leads Detail", "DYNAMIC", "Lead Follow Up"),
            # "leadFollowUp_add.html": ("Leads", reverse("leads"), "Leads Detail", "DYNAMIC", "Lead Follow Up", "FOLLOWUP_URL_ADD", "Add Follow Up"),
            # "leadFollowUp_edit.html": ("Leads", reverse("leads"), "Leads Detail", "DYNAMIC", "Lead Follow Up", "FOLLOWUP_URL_EDIT", "Edit Follow Up"),
            # "lead_all_followup.html": ("Leads", reverse("leads"), "All Follow Ups"),

            # "FollowupNotification.html": ("Follow Up Notifications", None),
            # "favourite_lead.html": ("Favourite Leads", None),
            # "Search.html": ("Search", None),
            # "Investors_list.html": ("Investors", None),
            # "dashboard.html": ("Dashboard", None),

            # "appointments_list.html": ("Appointments", reverse("appointments")),
            # "user_list.html": ("Users", None),
        }

        slug = self.kwargs.get("slug")
        pk = self.kwargs.get("pk")
        if 'id' in self.kwargs and 'detail' in self.request.path:
            context['view_only'] = 'true'
            context['id'] = self.kwargs['id']
        elif 'id' in self.kwargs and 'edit' in self.request.path:
            context['view_only'] = 'false'
            context['id'] = self.kwargs['id']
        else:
            context['view_only'] = 'false'
            context['id'] = ''

        route = route_map.get(template)
        if route:
            def resolve_url(item):
                if item == "DYNAMIC" and slug:
                    return reverse("leads-detail", kwargs={"slug": slug})
                elif item == "FOLLOWUP_URL_ADD" and slug and pk:
                    return reverse("leadFollowUp", kwargs={"slug": slug, "pk": pk})
                elif item == "FOLLOWUP_URL_EDIT" and slug and pk:
                    return reverse("leadFollowUp", kwargs={"slug": slug, "pk": id})
                return item if isinstance(item, str) else None

            i = 0
            while i < len(route):
                label = route[i]
                url = route[i + 1] if i + 1 < len(route) else None
                section(label, resolve_url(url))
                i += 2

            context["section_title"] = route[0]
            if len(route) >= 5:
                context["subsection_title"] = route[-1]

        context["slug"] = slug
        context["pk"] = pk
        context["breadcrumbs"] = breadcrumbs
        return context


def cors_media_serve(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    response = FileResponse(open(file_path, 'rb'))
    # response["Access-Control-Allow-Origin"] = "https://radhe.co.in"
    response["Access-Control-Allow-Credentials"] = "true"
    return response


def csrf_failure(request, reason=""):
    return render(request, "403_csrf.html", status=403)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password1 = request.data.get("new_password1")
        new_password2 = request.data.get("new_password2")

        if not user.check_password(current_password):
            return Response(
                {"success": False, "error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password1 != new_password2:
            return Response(
                {"success": False, "error": "New passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password1) < 6:
            return Response(
                {"success": False, "error": "Password must be at least 6 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password1)
        user.save()

        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )

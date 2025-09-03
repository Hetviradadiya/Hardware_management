from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils.timezone import make_aware, get_current_timezone

class DashboardStatsAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_admin = user.is_superuser or (user.role and user.role.name == "Admin") or (user.role and user.role.name == "Sales Head")

        # Filters
        prop_filter = Q()
        lead_filter = Q(is_deleted=False)
        followup_filter = Q()

        if not is_admin:
            lead_filter &= Q(created_by=user)
            followup_filter &= Q(follow_up_by=user)
            
        ten_days_ago = datetime.now().date() - timedelta(days=10)
        today = datetime.now().date()
        tomorrow = datetime.now().date() + timedelta(days=1)

        today_start_datetime = make_aware(datetime.combine(today, datetime.min.time()))
        today_end_datetime = make_aware(datetime.combine(today, datetime.max.time()))
        tomorrow_start_datetime = make_aware(datetime.combine(tomorrow, datetime.min.time()))
        tomorrow_end_datetime = make_aware(datetime.combine(tomorrow, datetime.max.time()))
        ten_days_ago_end_datetime = make_aware(datetime.combine(ten_days_ago, datetime.max.time()))
            
        # today_followups = LeadFollowUp.objects.filter(follow_up_date__range=(today_start_datetime, today_end_datetime), status__in=['open','hold'])
        # tomorrow_followups = LeadFollowUp.objects.filter(follow_up_date__range=(tomorrow_start_datetime, tomorrow_end_datetime), status__in=['open','hold'])
        # pending_leads = Lead.objects.filter(lead_followup_status='Pending')
        
        # if not is_admin:
        #     today_followups = today_followups.filter(follow_up_by=user)
        #     tomorrow_followups = tomorrow_followups.filter(follow_up_by=user)
        #     pending_leads = pending_leads.filter(created_by=user)

        # data = {
        #     "total_properties": Property.objects.filter(prop_filter).count(),
        #     "total_leads": Lead.objects.filter(lead_filter).count(),
        #     "upcoming_appointments": LeadFollowUp.objects.filter(followup_filter, follow_up_date__gte=today_start_datetime).count(),
        #     "closed_leads": Lead.objects.filter(lead_filter & Q(lead_followup_status="Closed")).count(),
        #     "total_users": UserAccount.objects.count() if is_admin else 0,
        #     "total_bookings": Lead.objects.filter(lead_filter & Q(lead_followup_status="Booking Done")).count(),
        #     "today_followups": today_followups.count(),
        #     "tomorrow_followups": tomorrow_followups.count(),
        #     "pending_leads": pending_leads.count(),
        #     "properties_ten": Property.objects.filter(created_at__gte=ten_days_ago_end_datetime).count(),
        # }

        # return Response(data)


# class RecentLeadsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         if request.user.role.name == "Admin" or (request.user.role and request.user.role.name == "Sales Head"):
#             leads = Lead.objects.filter(is_deleted=False).order_by('-created_at')[:10]
#         else:
#             leads = Lead.objects.filter(created_by=request.user, is_deleted=False).order_by('-created_at')[:10]
#         serializer = LeadSerializer(leads, many=True)
#         return Response(serializer.data)

import traceback
from collections import OrderedDict

class DashboardDataAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            key = request.GET.get("key")
            user_id = request.GET.get('user_id')

            ten_days_ago = datetime.now().date() - timedelta(days=10)
            today = datetime.now().date()
            tomorrow = datetime.now().date() + timedelta(days=1)

            today_start_datetime = make_aware(datetime.combine(today, datetime.min.time()))
            today_end_datetime = make_aware(datetime.combine(today, datetime.max.time()))
            tomorrow_start_datetime = make_aware(datetime.combine(tomorrow, datetime.min.time()))
            tomorrow_end_datetime = make_aware(datetime.combine(tomorrow, datetime.max.time()))
            ten_days_ago_end_datetime = make_aware(datetime.combine(ten_days_ago, datetime.max.time()))

            # queryset = Lead.objects.filter(is_deleted=False)
            # user = request.user
            # is_admin = user.is_superuser or (user.role and user.role.name == "Admin") or (user.role and user.role.name == "Sales Head")

            # # Filters
            # lead_filter = Q(is_deleted=False)
            # followup_filter = Q()

            # if not is_admin:
            #     lead_filter &= Q(created_by=user)
            #     followup_filter &= Q(follow_up_by=user)

            # if key == "today-followups":
            #     queryset = LeadFollowUp.objects.filter(
            #         followup_filter,
            #         follow_up_date__range=(today_start_datetime, today_end_datetime),
            #         status__in=['open','hold']
            #     ).distinct()
            #     if user_id and user_id.isdigit():
            #         queryset = queryset.filter(follow_up_by=user_id)

            # elif key == "tomorrow-followups":
            #     queryset = LeadFollowUp.objects.filter(
            #         followup_filter,
            #         follow_up_date__range=(tomorrow_start_datetime, tomorrow_end_datetime),
            #         status__in=['open','hold']
            #     ).distinct()
            #     if user_id and user_id.isdigit():
            #         queryset = queryset.filter(follow_up_by=user_id)

            # elif key == "pending-leads":
            #     queryset = queryset.filter(lead_filter, lead_followup_status="Pending")
            #     if user_id and user_id.isdigit():
            #         queryset = queryset.filter(created_by=user_id)
            #     raw_data = list(queryset.values(
            #         'id',
            #         'area_requirements',
            #         'purpose',
            #         'property_type__name',
            #         'name',
            #         'mobile',
            #         'mobile_2',
            #         'area',
            #         'requirements',
            #         'min_budget',
            #         'max_budget',
            #         'min_size',
            #         'max_size',
            #         'furnished_status',
            #         'created_by__full_name',
            #         'lead_followup_status',
            #     ))

            #     data = []
            #     for item in raw_data:
            #         formatted = OrderedDict()
            #         formatted['id'] = item.get('id')
            #         formatted['purpose'] = item.get('purpose', '').replace('_', ' ').title() if item.get('purpose', '') else ''
            #         formatted['area_requirements'] = item.get('area_requirements')
            #         formatted['property_type__name'] = item.get('property_type__name')
            #         formatted['name'] = item.get('name')
            #         formatted['mobile'] = item.get('mobile')
            #         formatted['mobile_2'] = item.get('mobile_2')
            #         formatted['area'] = item.get('area')
            #         formatted['requirements'] = item.get('requirements')
            #         formatted['min_budget'] = item.get('min_budget')
            #         formatted['max_budget'] = item.get('max_budget')
            #         formatted['min_size'] = item.get('min_size')
            #         formatted['max_size'] = item.get('max_size')
            #         formatted['furnished_status'] = item.get('furnished_status')
            #         formatted['created_by'] = item.get('created_by__full_name')
            #         formatted['status'] = item.get('lead_followup_status', '').replace('_', ' ').title() if item.get('lead_followup_status', '') else ''
            #         data.append(formatted)

            #     return Response(data)

            # elif key == "visits-scheduled":
            #     queryset = LeadFollowUp.objects.filter(followup_filter, follow_up_date__gte=today_start_datetime)
            #     if user_id and user_id.isdigit():
            #         queryset = queryset.filter(follow_up_by=user_id)
                
            # elif key == "properties-ten":
            #     queryset = Property.objects.filter(created_at__gte=ten_days_ago_end_datetime)

            #     data = list(queryset.values(
            #         'id',
            #         'address',
            #         'purpose',
            #         'title',
            #         'project__name',
            #         'super_built_up_area',
            #         'bhk',
            #         'price',
            #         'owner_name',
            #         'owner_number',
            #         'key_status',
            #         'furnished_status',
            #         'status',
            #     ))

            #     final_data = []
            #     for item in data:
            #         formatted = {
            #             'id': item.get('id'),
            #             'address': item.get('address', ''),
            #             'purpose': item.get('purpose', '').replace('_', ' ').title() if item.get('purpose', '') else '',
            #             'block_number': item.get('title', ''),
            #             'project_name': item.get('project__name', ''),
            #             'super_built_up_area': item.get('super_built_up_area', ''),
            #             'bhk': item.get('bhk', ''),
            #             'price': item.get('price', ''),
            #             'owner_name': item.get('owner_name', ''),
            #             'owner_number': item.get('owner_number', ''),
            #             'key_status': item.get('key_status', ''),
            #             'furnished_status': item.get('furnished_status', ''),
            #             'status': item.get('status', ''),
            #         }
            #         final_data.append(formatted)

            #     return Response(final_data)

            # else:
            #     return Response({"error": "Invalid key"}, status=400)

            # serializer = LeadDashboardSerializer(queryset, many=True)
            # return Response(serializer.data)
        except Exception as e:
            print(traceback.format_exc())
            return Response({"error": str(e)}, status=500)

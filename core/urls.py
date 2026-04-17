from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('admin_reservations/<int:id>/status/', views.update_reservation_status, name='update_reservation_status'),
    path('admin_reservations/<int:id>/delete/', views.delete_reservation, name='delete_reservation'),
    path('facilities/', views.facilities_view, name='facilities'),
    path('ajax/check_availability/', views.check_availability, name='check_availability'),

    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_facilities/', views.admin_facilities, name='admin_facilities'),
    path('admin/facility/delete/<int:id>/', views.delete_facility, name='delete_facility'),
    path('admin_equipments/', views.admin_equipments, name='admin_equipments'),
    path('admin_equipment/delete/<int:id>/', views.delete_equipment, name='delete_equipment'),
    path('admin_users/', views.admin_users, name='admin_users'),
    path("users/edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("users/delete/<int:user_id>/", views.delete_user, name="delete_user"),
    path('admin_reservations/', views.admin_reservations, name='admin_reservations'),
    path('admin_booking_detail/<int:id>/', views.admin_booking_detail, name='admin_booking_detail'),
    path('admin_settings/', views.admin_settings, name='admin_settings'),

    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:id>/read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    # path('notifications/<int:id>/read/', views.mark_single_notification_read, name='mark_single_notification_read'),

    path('logout/', views.logout_view, name='logout'),
]

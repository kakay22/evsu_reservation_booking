from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Notification, User, Facility, Equipment, Reservation, ReservationEquipment

# ---------- CUSTOM USER ADMIN ----------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

# ---------- FACILITY ADMIN ----------
@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'is_active')
    search_fields = ('name', 'location')
    list_filter = ('is_active',)

# ---------- EQUIPMENT ADMIN ----------
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'is_active')
    search_fields = ('name', 'category')
    list_filter = ('category', 'is_active')

# ---------- RESERVATION ADMIN ----------
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('facility', 'user', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'facility', 'date')
    search_fields = ('user__username', 'facility__name', 'notes')
    ordering = ('-date', 'start_time')

# ---------- RESERVATION EQUIPMENT ADMIN ----------
@admin.register(ReservationEquipment)
class ReservationEquipmentAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'equipment', 'quantity')
    search_fields = ('reservation__user__username', 'equipment__name')
    list_filter = ('equipment',)

admin.site.register(Notification)
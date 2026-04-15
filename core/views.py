from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import Reservation, Facility, ReservationEquipment, Equipment, Notification
from django.db import IntegrityError
from allauth.socialaccount.models import SocialApp

from .forms import ReservationForm


from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


# ---------- HOME ----------
def home(request):
    return render(request, 'core/home.html')


# ---------- REGISTER ----------
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Proper User instance

            # ✅ CREATE ADMIN NOTIFICATION
            User = get_user_model()
            admins = User.objects.filter(is_superuser=True)

            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    message=f"New user registered: {user.username}",
                    type='user',
                    target_audience='admin'
                )

            # Authenticate immediately
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                messages.success(request, "Account created successfully!")
                return redirect('user_dashboard')
            else:
                messages.error(request, "Error logging in after registration.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    social_providers = {}
    try:
        social_providers['google'] = SocialApp.objects.get(provider='google')
    except SocialApp.DoesNotExist:
        social_providers['google'] = None

    return render(request, 'core/register.html', {
        'form': form,
        'socialaccount_providers': social_providers,
    })


def login_view(request):
    # auto login if authenticated (redirect to appropriate dashboard)
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('user_dashboard')

    # ---------- LOGIN ----------
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.is_superuser:
                messages.success(request, "Logged in successfully!")
                return redirect('admin_dashboard')
            else:
                messages.success(request, "Logged in successfully!")
                return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()

    social_providers = {}
    try:
        social_providers['google'] = SocialApp.objects.get(provider='google')
    except SocialApp.DoesNotExist:
        social_providers['google'] = None

    return render(request, 'core/login.html', {
        'form': form,
        'socialaccount_providers': social_providers,
    })


# ---------- USER DASHBOARD ----------
@login_required
def user_dashboard(request):
    user = request.user
    today = timezone.now().date()

    reservations = Reservation.objects.filter(user=user)

    context = {
        'total_reservations': reservations.count(),
        'pending_approvals': reservations.filter(status='pending').count(),
        'upcoming_reservations': reservations.filter(date__gte=today).count(),
        'recent_reservations': [
            {
                'facility': r.facility,
                'date': r.date,
                'status': r.status,
                'time_slot': f"{r.start_time.strftime('%I:%M %p')} - {r.end_time.strftime('%I:%M %p')}",
                'notes': r.notes,
            } for r in reservations.order_by('-date', '-start_time')[:5]
        ]
    }
    return render(request, 'user/user_dashboard.html', context)

@login_required
def my_reservations(request):
    user = request.user
    today = timezone.now().date()

    # ---------- HANDLE FORM ----------
    if request.method == "POST":
        form = ReservationForm(request.POST)

        if form.is_valid():
            try:
                reservation = form.save(commit=False)
                reservation.user = user
                reservation.status = "pending"
                reservation.save()

                # -----------------------------
                # 👤 USER NOTIFICATION
                # -----------------------------
                Notification.objects.create(
                    user=user,
                    message=f"Your reservation for {reservation.facility.name} on {reservation.date} is pending approval.",
                    type="reservation",
                    target_audience="user",
                    reservation=reservation
                )

                # -----------------------------
                # 🧑‍💼 ADMIN NOTIFICATION
                # -----------------------------
                admin_users = User.objects.filter(is_superuser=True)

                for admin in admin_users:
                    Notification.objects.create(
                        user=admin,
                        message=f"New reservation from {user.username} for {reservation.facility.name} on {reservation.date}.",
                        type="reservation",
                        target_audience="admin",
                        reservation=reservation
                    )

                # 🔥 IMPORTANT: Clear existing equipment (safe for reuse/edit logic)
                ReservationEquipment.objects.filter(reservation=reservation).delete()

                # ✅ Save selected equipment
                equipments = form.cleaned_data.get('equipment')
                if equipments:
                    equipment_bulk = [
                        ReservationEquipment(
                            reservation=reservation,
                            equipment=eq,
                            quantity=1
                        )
                        for eq in equipments
                    ]
                    ReservationEquipment.objects.bulk_create(equipment_bulk)

                messages.success(
                    request,
                    f"Reservation for {reservation.facility.name} on {reservation.date} submitted successfully!"
                )

                return redirect('my_reservations')

            except IntegrityError:
                messages.error(
                    request,
                    "This time slot is already booked or conflicts with another reservation."
                )

            except Exception as e:
                messages.error(
                    request,
                    "Something went wrong. Please try again."
                )

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ReservationForm()

    # ---------- FETCH RESERVATIONS ----------
    reservations = (
        Reservation.objects
        .filter(user=user)
        .select_related('facility')
        .prefetch_related('equipments__equipment')  # 🔥 include equipment
        .order_by('-date', '-start_time')
    )

    # Add formatted data
    for res in reservations:
        res.time_slot = f"{res.start_time.strftime('%I:%M %p')} - {res.end_time.strftime('%I:%M %p')}"
        res.equipment_list = [eq.equipment.name for eq in res.equipments.all()]

    # ---------- FACILITIES ----------
    facilities = Facility.objects.filter(is_active=True)

    context = {
        'reservations': reservations,
        'form': form,
        'facilities': facilities,
    }

    return render(request, 'user/my_reservations.html', context)

# ---------- BOOKING DETAIL ----------
@login_required
def admin_booking_detail(request, id):
    reservation = get_object_or_404(
        Reservation.objects.select_related('user', 'facility')
        .prefetch_related('equipments__equipment'),
        id=id
    )

    return render(request, 'admin/booking_detail.html', {
        'reservation': reservation
    })

@login_required
def facilities_view(request):
    facilities = Facility.objects.filter(is_active=True)
    today = timezone.now().date()

    # Handle booking via modal
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.status = "pending"
            try:
                reservation.full_clean()  # Validate constraints
                reservation.save()
                messages.success(request, f"Reservation for {reservation.facility.name} on {reservation.date} submitted!")
                return redirect('facilities')
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReservationForm()

    context = {
        'facilities': facilities,
        'form': form,
        'today': today,
    }
    return render(request, 'user/facilities.html', context)

from django.http import JsonResponse
from datetime import datetime
from django.views.decorators.http import require_GET

@require_GET
@login_required
def check_availability(request):
    """
    AJAX endpoint to return booked time slots for a given facility & date.
    """
    facility_id = request.GET.get('facility_id')
    date_str = request.GET.get('date')

    if not facility_id or not date_str:
        return JsonResponse({"error": "Missing parameters"}, status=400)

    try:
        facility = Facility.objects.get(id=facility_id)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Facility.DoesNotExist:
        return JsonResponse({"error": "Facility not found"}, status=404)
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    reservations = Reservation.objects.filter(facility=facility, date=date)
    booked_slots = [{"start_time": r.start_time.strftime("%H:%M"), 
                     "end_time": r.end_time.strftime("%H:%M")} for r in reservations]

    return JsonResponse({"booked_slots": booked_slots})

User = get_user_model()

# ---------- ADMIN CHECK ----------
def is_admin(user):
    return user.is_authenticated and user.is_superuser

# ---------- ADMIN DASHBOARD ----------
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    # GET FILTER
    status = request.GET.get("status", "all")

    # BASE QUERY
    reservations = Reservation.objects.select_related('user', 'facility').order_by('-created_at')

    # APPLY FILTER
    if status != "all":
        reservations = reservations.filter(status=status)

    # LIMIT RESULTS
    reservations = reservations[:10]

    # STATS
    total_users = User.objects.filter(is_superuser=False).count()
    total_facilities = Facility.objects.count()
    total_reservations = Reservation.objects.count()
    pending_reservations = Reservation.objects.filter(status="pending").count()
    approved_reservations = Reservation.objects.filter(status="approved").count()
    rejected_reservations = Reservation.objects.filter(status="rejected").count()

    # FORMAT TIME SLOT
    for res in reservations:
        res.time_slot = f"{res.start_time.strftime('%I:%M %p')} - {res.end_time.strftime('%I:%M %p')}"

    context = {
        "total_users": total_users,
        "total_facilities": total_facilities,
        "total_reservations": total_reservations,
        "pending_reservations": pending_reservations,
        "approved_reservations": approved_reservations,
        "rejected_reservations": rejected_reservations,
        "recent_reservations": reservations,
        "status_filter": status,   # IMPORTANT FOR TABS
    }

    return render(request, "admin/admin_dashboard.html", context)


# ---------- USERS MANAGEMENT ----------
@login_required
@user_passes_test(is_admin)
def admin_users(request):
    users = User.objects.exclude(username="evsuadmin")
    return render(request, "admin/admin_users.html", {"users": users})



User = get_user_model()

def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.role = request.POST.get("role")

        user.save()
        messages.success(request, "User updated successfully!")
        return redirect("admin_users")

    return render(request, "admin/edit_user.html", {"user": user})

from django.contrib.auth.decorators import login_required

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully!")
        return redirect("admin_users")

    return render(request, "admin/confirm_delete.html", {"user": user})

# ---------- FACILITIES MANAGEMENT ----------
@login_required
@user_passes_test(is_admin)
def admin_facilities(request):
    facilities = Facility.objects.all()
    return render(request, "admin/admin_facilities.html", {"facilities": facilities})

# ---------- RESERVATIONS MANAGEMENT ----------
@login_required
@user_passes_test(is_admin)
def admin_reservations(request):
    reservations = Reservation.objects.select_related("user", "facility").order_by("-date", "-start_time")
    return render(request, "admin/admin_reservations.html", {"reservations": reservations})

@csrf_exempt
def update_reservation_status(request, id):
    if request.method == "POST":
        data = json.loads(request.body)
        status = data.get("status")

        from .models import Reservation
        res = Reservation.objects.get(id=id)

        if status in ["approved", "rejected"]:
            res.status = status
            res.save()
            return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)


@csrf_exempt
def delete_reservation(request, id):
    if request.method == "POST":
        from .models import Reservation
        Reservation.objects.filter(id=id).delete()
        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)


# ---------- ADMIN SETTINGS ----------
@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, "Password updated successfully!")
            return redirect("admin_settings")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "admin/admin_settings.html", {"form": form})


from django.http import JsonResponse
from .models import Notification
from django.contrib.auth.decorators import login_required

@login_required
def get_notifications(request):

    base_query = Notification.objects.filter(
        user=request.user,
        target_audience__in=["admin", "both"] if request.user.is_superuser else ["user", "both"]
    )

    # 🔥 unread count
    unread_count = base_query.filter(is_read=False).count()

    # 🔥 latest notifications
    notifications = base_query.order_by('-created_at')[:10]

    data = [
        {
            "id": n.id,
            "message": n.message,
            "type": n.type,
            "time": n.created_at.strftime("%b %d, %I:%M %p"),
            "is_read": n.is_read,

            # 🔥 THIS IS THE MISSING PIECE (CRITICAL FIX)
            "reservation_id": n.reservation.id if n.reservation else None
        }
        for n in notifications
    ]

    return JsonResponse({
        "notifications": data,
        "unread_count": unread_count
    })

@login_required
def mark_notification_as_read(request, id):
    if request.method == "POST":
        notif = get_object_or_404(Notification, id=id, user=request.user)
        notif.is_read = True
        notif.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)

@login_required
def mark_single_notification_read(request, id):
    if request.method == "POST":
        notif = get_object_or_404(Notification, id=id, user=request.user)
        notif.is_read = True
        notif.save()

        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('home')  # make sure 'home' exists in your urls
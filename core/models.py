from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from datetime import datetime

# ---------- USERS ----------
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    email = models.EmailField(unique=True)

    # Avoid conflicts with default auth
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set_permissions',
        blank=True,
        verbose_name='user permissions'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin_user(self):
        return self.role == 'admin'

    @property
    def is_staff_user(self):
        return self.role == 'staff'

    @property
    def is_student_user(self):
        return self.role == 'student'


# ---------- FACILITIES ----------
class Facility(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='facilities/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ---------- EQUIPMENT ----------
class Equipment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='equipment/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ---------- RESERVATIONS ----------
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='reservations')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='reservations')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['facility', 'date', 'start_time', 'end_time'],
                name='unique_reservation'
            )
        ]
        ordering = ['-date', 'start_time']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

    @property
    def duration(self):
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return end - start

    def __str__(self):
        return f"{self.facility.name} reserved by {self.user.username} on {self.date}"


# ---------- RESERVATION-EQUIPMENT LINK ----------
class ReservationEquipment(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='equipments')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='reservations')
    quantity = models.PositiveIntegerField(default=1)

    def clean(self):
        if self.quantity > self.equipment.quantity:
            raise ValidationError(f"Cannot reserve more than {self.equipment.quantity} units of {self.equipment.name}")

    def __str__(self):
        return f"{self.equipment.name} for {self.reservation}"
    
class Notification(models.Model):
    reservation = models.ForeignKey(
        'Reservation',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    NOTIFICATION_TYPES = [
        ('reservation', 'Reservation'),
        ('user', 'User Registration'),
        ('approval', 'Approval'),
        ('rejection', 'Rejection'),
    ]

    TARGET_AUDIENCE = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('both', 'Both'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)

    # NEW: who should see this notification
    target_audience = models.CharField(
        max_length=10,
        choices=TARGET_AUDIENCE,
        default='user'
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.user.username}"
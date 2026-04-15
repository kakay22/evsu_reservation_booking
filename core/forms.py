from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Reservation, Equipment
from datetime import date
from django.core.exceptions import ValidationError

# ---------- REGISTER FORM ----------
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={"class":"w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400 transition"}
    ))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = "w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400 transition"


# ---------- LOGIN FORM ----------
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs={"class":"w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400 transition"}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={"class":"w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-400 transition"}
    ))

class ReservationForm(forms.ModelForm):

    # ✅ Add equipment field
    equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        })
    )

    class Meta:
        model = Reservation
        fields = ['facility', 'date', 'start_time', 'end_time', 'notes']  # keep clean
        widgets = {
            'facility': forms.Select(attrs={
                'class': 'border rounded-lg px-4 py-2 w-full'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'border rounded-lg px-4 py-2 w-full'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'border rounded-lg px-4 py-2 w-full'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'border rounded-lg px-4 py-2 w-full'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'border rounded-lg px-4 py-2 w-full'
            }),
        }

    # ✅ Date validation
    def clean_date(self):
        d = self.cleaned_data.get('date')
        if d and d < date.today():
            raise forms.ValidationError("You cannot book a reservation in the past.")
        return d

    # ✅ Full form validation
    def clean(self):
        cleaned_data = super().clean()

        facility = cleaned_data.get('facility')
        date_ = cleaned_data.get('date')
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        # Time validation
        if start and end and start >= end:
            raise ValidationError("Start time must be before end time.")

        # Overlap validation
        if facility and date_ and start and end:
            conflicts = Reservation.objects.filter(
                facility=facility,
                date=date_,
                start_time__lt=end,
                end_time__gt=start
            )

            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                raise ValidationError(
                    "This time slot is already booked for the selected facility."
                )

        return cleaned_data
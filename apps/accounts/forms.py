import logging
from django.conf import settings
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter
from .models import UserProfile, create_activation_key, UserIdentificationLabel
from django.contrib.auth.forms import AuthenticationForm, UsernameField


logger = logging.getLogger('hhs_server.%s' % __name__)


class IdentificationModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=255,
                             label=_("Email"))
    first_name = forms.CharField(max_length=100,
                                 label=_("First Name"))
    last_name = forms.CharField(max_length=100,
                                label=_("Last Name"))
    organization_name = forms.CharField(max_length=100,
                                        label=_("Organization Name"),
                                        required=True
                                        )
    password1 = forms.CharField(widget=forms.PasswordInput,
                                max_length=120,
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput,
                                max_length=120,
                                label=_("Password (again)"))
    identification_choice = IdentificationModelChoiceField(label="Your Role", empty_label=None,
                                                           queryset=UserIdentificationLabel.objects.order_by('weight').all())

    required_css_class = 'required'

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'organization_name', 'password1', 'password2', 'identification_choice')

    def clean_email(self):
        email = self.cleaned_data.get('email', "")
        if email:
            if User.objects.filter(Q(email=email) | Q(username=email)).exists():
                raise forms.ValidationError(
                    _('This email address is already registered.'))
            return email.rstrip().lstrip().lower()
        else:
            return email.rstrip().lstrip().lower()

    def save(self):
        self.instance.username = self.instance.email
        self.instance.is_active = False
        user = super().save()

        UserProfile.objects.create(user=user,
                                   organization_name=self.cleaned_data[
                                       'organization_name'],
                                   user_type="DEV",
                                   create_applications=True)

        # TODO why do we do this (associate every user with a default patient)?
        # Attach the user to the default patient.
        Crosswalk.objects.create(user=user, fhir_source=get_resourcerouter(),
                                 fhir_id=settings.DEFAULT_SAMPLE_FHIR_ID)

        group = Group.objects.get(name='BlueButton')
        user.groups.add(group)

        # Assign user to identification label
        ident = self.cleaned_data['identification_choice']
        ident.users.add(user)
        ident.save()

        # Send a verification email
        create_activation_key(user)

        return user


class AccountSettingsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AccountSettingsForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(max_length=255, label=_('Email'), disabled=True, required=False)
    first_name = forms.CharField(max_length=100, label=_('First Name'))
    last_name = forms.CharField(max_length=100, label=_('Last Name'))
    organization_name = forms.CharField(max_length=100,
                                        label=_('Organization Name'),
                                        required=True)
    create_applications = forms.BooleanField(initial=False,
                                             required=False)
    required_css_class = 'required'


class AuthenticationForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True}),
                             max_length=150, label=_('Email'))
    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password."
        ),
        'inactive': _("This account is inactive."),
    }

    required_css_class = 'required'

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        return username.rstrip().lstrip().lower()

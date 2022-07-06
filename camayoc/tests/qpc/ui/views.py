"""Quipucords views."""
from smartloc import Locator
from widgetastic.widget import TextInput
from widgetastic.widget import View
from widgetastic_patternfly import Button
from widgetastic_patternfly import NavDropdown
from widgetastic_patternfly import VerticalNavigation


class LoginView(View):
    """Login view."""

    login = Button("Log In", classes=[Button.PRIMARY])
    username = TextInput(locator="#id_username")
    password = TextInput(locator="#id_password")


class DashboardView(View):
    """Dashboard view."""

    user_dropdown = NavDropdown(locator=Locator(css="li.dropdown:nth-child(2)"))
    logout = Button("Log out")
    nav = VerticalNavigation(locator=(Locator(css=".list-group")))


class ModalView(View):
    """Base class for modals."""

    cancel_button = Button("Cancel")


class SourceModalView(ModalView):
    """Base class for source modals."""

    next_button = Button("Next")
    back_button = Button("Back")
    close_button = Button(classes=["close"])


class CredentialModalView(ModalView):
    """Base class for credential modals."""

    save_button = Button("Save")


class DeleteModalView(ModalView):
    """Class for deletion dialogs."""

    delete_button = Button("Delete", classes=[Button.PRIMARY])

"""Quipucords views."""
from smartloc import Locator

from widgetastic.widget import TextInput, View

from widgetastic_patternfly import Button, NavDropdown, VerticalNavigation


class LoginView(View):
    """Login view."""

    login = Button('Log In', classes=[Button.PRIMARY])
    username = TextInput(locator='#id_username')
    password = TextInput(locator='#id_password')


class DashboardView(View):
    """Dashboard view."""

    user_dropdown = NavDropdown(
        locator=Locator(css='li.dropdown:nth-child(2)'))
    logout = Button('Log out')
    left_nav = VerticalNavigation(
            locator=(Locator(css='.nav-pf-vertical')))


class ModalView(View):
    """Base class for modal pages."""

    next_button = Button('Next')
    back_button = Button('Back')
    cancel_button = Button('Cancel')
    close_button = Button(classes=['close'])

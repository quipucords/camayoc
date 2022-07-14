UI tests framework
==================

.. caution::
   This documentation focuses on UI testing framework that uses `Playwright <https://playwright.dev/python/>`_.
   Older framework, built on top of `Selenium <https://www.selenium.dev/>`_, is briefly documented in project README file.


Preparing Playwright environment
--------------------------------

Before running Playwright-based tests, Playwright environment must be prepared.
In Camayoc virtual environment, run:

.. sourcecode:: shell

   playwright install

Playwright on Linux (and other operating systems?) requires certain system-level dependencies to be met. You can install them with command:

.. sourcecode:: shell

   playwright install-deps

Add ``--dry-run`` to see what Playwright wants to install.

You can verify that Playwright is set up correctly by running:

.. sourcecode:: shell

   playwright cr 'https://redhat.com'  # Opens Chromium
   playwright ff 'https://redhat.com'  # Opens Firefox
   playwright wk 'https://redhat.com'  # Opens WebKit

.. note:: Running Firefox on Fedora

   Offically, Playwright supports only Ubuntu LTS releases.
   ``playwright ff`` might error out on Fedora system.
   The fix is to use system-wide libstdc++:

   .. sourcecode:: shell

      rm ~/.cache/ms-playwright/firefox-1323/firefox/libstdc++.so.6
      ln -s /usr/lib64/libstdc++.so.6 ~/.cache/ms-playwright/firefox-1323/firefox/libstdc++.so.6

   You might have different version of Firefox, so change directory name above accordingly.


Running existing UI tests
-------------------------

Use pytest, just like for all the other tests:

.. sourcecode:: shell

   pytest camayoc/tests/qpc/ui/test_endtoend.py::test_demo_endtoend -s -v

By default, Playwright will run tests in **headless** mode, i.e. you won't see anything. Add ``--headed`` to see what Playwright is doing.

Playwright tries to run tests in all three supported engines (Chromium, Firefox, WebKit). Add ``--browser chromium`` to run tests using specific browser.

See `pytest-playwright <https://playwright.dev/python/docs/test-runners#cli-arguments>`_ documentation for list of all supported command-line options.
Playwright also maintains a page with `debugging tips <https://playwright.dev/python/docs/debug>`_.


Framework building blocks
-------------------------

Let's discuss the building blocks of the framework.
Some parts of this section might be clearer after reading "Design decisions" section below, but the same is true for that section.
"What?" and "Why?" are kind of intertwined.

Client
^^^^^^

Similar to API and CLI interfaces, there's ``camayoc.ui.Client`` class representing UI client.
This is your main entry point to interact with Quipucords web interface.
It wraps Playwright's ``Page`` class (which represents single tab in the browser) and coordinates work of few other classes.
``ui_client`` pytest fixture returns ``Client`` instance. Each test will get new instance with completely new browser window.
Starting browser in Playwright is fast, so there's little reason to re-use browser between tests.

Page models
^^^^^^^^^^^

In accordance with Page Object Model design pattern, each page is represented by single class.

Page objects aim to make tests more maintainable by limiting the number of places where changes must be made.
For example, most tests would need to log in at the beginning. If you use Playwright directly, your test could look like that:

.. sourcecode:: text

   client.driver.fill("#username", username)
   client.driver.fill("#password", password)
   client.driver.click("#login")

Now imagine that "Log in" button id attribute changed from ``login`` to ``submit``. Suddenly you need to change element locator in all tests.

With page objects, the code above is moved to ``login`` method of ``LoginPage`` object, and tests will look like that:

.. sourcecode:: text

   LoginPage().login(username, password)

When element on page changes, there's limited number of places that have to be changed - ideally, there will be only one such place.

Page objects should provide methods that define actions that user can make on specific page.
In Camayoc, we err on the side of higher level actions. So ``LoginPage`` will have single ``login()`` method, instead of triplet of ``fill_username()``, ``fill_password()`` and ``submit_form()`` methods.
The idea is that after performing an action, browser should be left in a state where it's reasonable to take another action.
Another idea is that actions should make sense on their own and should not require other actions to complete before they can be invoked.
(Note that this applies to interface itself and not business logic of Quipucords.
It doesn't make much sense to go to Scans before creating Source, but UI allows user to do that, so framework should expose such action.)

Chains of related actions should be wrapped in "page service" methods.
These allow to write shorter tests, which is especially important for code that sets up the stage for actual verification.
For example, creating new source requires filling two forms in three-step wizard.
``SourcePage`` may expose ``create_source`` "service", which essentially does:

.. sourcecode:: text

   SourcePage()
     .open_add_source_wizard()
     .fill(wizard_step1_data)
     .next_step()
     .fill(wizard_step2_data)
     .next_step()
     .close_wizard()


Page components
"""""""""""""""

Some components are common to multiple pages, like vertical menu or logout button.
In Camayoc, we separate these into mixin classes and use multiple inheritance to compose pages with shared capabilities.
Multiple inheritance is preferred over composition, because it allows to skip method-forwarding code. Compare:

.. sourcecode:: python
   :caption: Composition

   class VerticalNavigationComponent(AbstractPage):
       def navigate_to(self, destination):
           ...

   class LogoutComponent(AbstractPage):
       def logout(self):
           ...

   class SourcePage(AbstractPage):
       def __init__(self):
           self.vertical_nav_component = VerticalNavigationComponent()
           self.logout_component = LogoutComponent()

       def navigate_to(self, destination):
           self.vertical_nav_component.navigate_to(destination)

       def logout(self):
           self.logout_component.logout()

.. sourcecode:: python
   :caption: Multiple inheritance

   class VerticalNavigationComponent:
       def navigate_to(self, destination):
           ...

   class LogoutComponent:
       def logout(self):
           ...

   class SourcePage(LogoutComponent, VerticalNavigationComponent, AbstractPage):
       # mro takes care of calling VerticalNavigationComponent.navigate_to()
       # and LogoutComponent.logout()
       ...


Forms
"""""

Forms handling is highly inspired by Django / Django REST Framework.

Page object that contains a form should inherit ``camayoc.ui.models.components.form.Form`` component.
They should also define class ``FormDefinition`` as class property.
``FormDefinition`` should contain properties for each form field.
Property name should match input data object attribute name (see below), and property value should be an instance of class that inherit from ``Field`` class.
``Field`` class instantiation takes two arguments: selector that finds this specific field on this specific page, and optional function that may be used to transform input data into something that Playwright can understand.

Complete basic example:

.. sourcecode:: python

   from .abstract_page import AbstractPage
   from ..components.form import Form
   from ..fields import InputField


   class SomeForm(Form, AbstractPage):
        class FormDefinition:
            user_id = InputField("input#id", lambda i: str(i))

Types
^^^^^

All page methods should take up to one additional argument.
This argument should be either an enum, or an instance of special data-input class (DTO).
We use ``enum`` module from Python standard library for enums, and `attrs <https://www.attrs.org/>`_ for data-input classes.

There are three main reasons for that.
First, to limit the space of values that methods need to work with.
We don't want to obfuscate page object methods with input validation logic.
Page object methods should be able to assume that their arguments have certain properties, and type hints are the easiest way of achieving that.

Second, to catch data input mistakes early.
When data is transferred with dictionaries, typos in key names and missing required keys are discovered only at runtime.
This is frustrating for test developers, especially if mistake was made relatively late in the test and they have to wait a long time before fix may be verified.
With strongly-typed input, your editor should notify you that method input is of wrong type, and mistakes can be corrected much earlier.

Third, there are libraries to generate objects with random data.

Example below shows how to use enum as method input, how to create simple DTO and how to create complex DTO.

.. sourcecode :: python

   from camayoc.ui.types import AddCredentialDTO
   from camayoc.ui.types import LoginFormDTO
   from camayoc.ui.types import SSHNetworkCredentialFormDTO
   from camayoc.ui.enums import CredentialTypes
   from camayoc.ui.enums import MainMenuPages
   from camayoc.ui.enums import NetworkCredentialBecomeMethods
   from camayoc.utils import uuid4

   SourcesMainPage().navigate_to(MainMenuPages.CREDENTIALS)

   login_data = LoginFormDTO(username='admin', password='admin')

   credential_data = AddCredentialDTO(
       credential_type=CredentialTypes.NETWORK,
       credential_form_dto=SSHNetworkCredentialFormDTO(
           credential_name="my credential name " + uuid4(),
           username="username" + uuid4(),
           ssh_key_file="/root/.bashrc",
           passphrase="supersecretpassword" + uuid4(),
           become_method=NetworkCredentialBecomeMethods.PFEXEC,
           become_user="systemusername" + uuid4(),
           become_password="systemsecretpassword" + uuid4(),
       ),
   )

Creating random test data
^^^^^^^^^^^^^^^^^^^^^^^^^

Camayoc uses `factory_boy <https://factoryboy.readthedocs.io/>`_ to generate DTOs with random data.
factory_boy uses `Faker <https://faker.readthedocs.io/>`_ under the hood.

factory_boy provides highly declarative syntax and allows for related fields, i.e. cases where value of one field is constrained on value of another field.
It's easy to generate complete objects, and it's easy to specify values of selected fields.

Example below shows how to create simple DTO, how to specify value for single field and how to create complex DTO while setting value in related object.

.. sourcecode :: python

   from camayoc.ui.data_factories import LoginFormDTOFactory
   from camayoc.ui.data_factories import AddCredentialDTOFactory
   from camayoc.ui.data_factories import AddSourceDTOFactory
   from camayoc.ui.enums import SourceTypes

   login_data = LoginFormDTOFactory()

   credential_data = AddCredentialDTOFactory(credential_type=credential_type)

   source_data = AddSourceDTOFactory(
       select_source_type__source_type=SourceTypes.SATELLITE,
       source_form__credentials=[credential_data.credential_form_dto.credential_name],
   )

Design decisions
----------------

Here's the overview of framework goals, and brief explanation behind certain design decisions.

**Leverage well-known Page Object Model design pattern**
   Let's not reinvent the wheel.
   Anyone with experience in UI testing is familiar with Page Object Model.
   There are many articles, videos and tutorials explaining it.
   Make it easy for the next person.

   The same drive towards familiarity is behind form design and choice of factory_boy and Faker.

**Leverage static analysis to catch mistakes early**
   UI tests have bad reputation because they tend to be slow, and that makes their feedback loop long.
   Simple mistake, like typo in input dictionary key, can easily cost 10 minutes, if it takes few minutes to run the test.

   By heavy usage of type hints and strongly-typing method arguments, we hope that most of simple mistakes will be caught by editor, way before test is executed.

**Make tests succinct**
   Page objects "service methods" and DTO factories allow for writing relatively short tests.

**Make common things easy...**
   Most of tests are "happy-path tests", that only concern themselves with verifying that something may work in optimistic scenario.
   It should be easy and fast to write tests like these.

   That's why page object methods focus on actual working actions and we don't provide methods for actions that result in invalid state of the system.

**...and exceptional things possible**
   At the same time, framework should not prevent test author from checking exceptions and reactions to invalid data.

   That's why client exposes driver object.
   At any point of test, author can go to lower level and interact with page directly.

**Allow for High Volume Automated Testing**
   Most of tests verifies single, direct path through the system. Randomness, if any, is only in input data.

   High Volume Automated Testing is the idea of writing tests that randomly journey through the system.
   Instead of having specific goal, they run for specified amount of time.
   They perform actions that should succeed, and inform the team when they encounter exceptions.

   HiVAT are intended to find issues that become apparent only when using system for extended period of time - memory leaks, gradually worsening performance, unoptimized data access, assumptions about stored data size etc.

   Framework is designed to make HiVAT possible.
   That's why we use a special form of Page Object Model, called Fluent Page Object Model.
   In Fluent POM, each method should return a page object.
   This makes it possible to chain method calls to model user journey through the system.

   Some methods may require arguments.
   That's why framework expects all methods arguments to be type-hinted - so HiVAT could inspect method signature and use factories to generate required data.
   That's also why factories should generate data that is valid.

   Proof of concept of HiVAT is implemented in ``camayoc/tests/qpc/ui/test_long_running.py``.

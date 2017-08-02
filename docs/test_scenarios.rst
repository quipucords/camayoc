==============
Test Scenarios
==============

.. contents:: List of test scenarios
   :depth: 2
   :local:

----
Auth
----

rho auth add
============

Add auth with required options
------------------------------

:description: Add an auth entry providing only the required options ``--name``
              and ``--username``
:steps: Run ``rho auth add --name <name> --username <username>``
:expectedresults: A new auth entry is created and the name and username must be
                  the same as the input. Also the entry must be available on
                  the ``credentials`` file.

Add auth with additional options
--------------------------------

:description: Add an auth entry providing the additional options other than the
              required ones, ``--name`` and ``--username``. The additional
              options are: ``--sshkeyfile``, ``--password`` and ``--vault``.
:steps: Run ``rho auth add --name <name> --username <username> --sshkeyfile
        <sshkeyfilepath> --password --vault <vault>``
:expectedresults: A new auth entry is created and data must be the same as the
                  input. Also the entry must be available on the
                  ``credentials`` file.

Add auth with vault
-------------------

:description: Add an auth entry providing the required options ``--name``
              and ``--username`` passing the ``--vault`` option.
:steps: Run ``rho auth add --name <name> --username <username> --vault
        <vault>``
:expectedresults: A new auth entry is created and the name and username must be
                  the same as the input. Also the entry must be available on
                  the ``credentials`` file.

Add auth with invalid sshkeyfile (negative)
-------------------------------------------

:description: Add an auth entry providing the additional options, with invalid
              values, other than the required ones, ``--name`` and
              ``--username``. The additional options are: ``--sshkeyfile`` and
              ``--password``.
:steps: Run ``rho auth add --name <name> --username <username> --sshkeyfile
        <invalidsshkeyfilepath> --password``
:expectedresults: The command must fail and provide an error message stating
                  what went wrong. Also no entry must be created on the
                  ``credentials`` file.

Add auth with vault (negative)
------------------------------

:description: Add an auth entry providing the required options ``--name`` and
              ``--username`` passing an invalid value for the ``--vault``
              option.
:steps: Run ``rho auth add --name <name> --username <username> --vault
        <invalidvault>``
:expectedresults: No auth entry is created and the ``credentials`` file is not
                  updated.
:bug: https://github.com/quipucords/rho/issues/132

rho auth clear
==============

Clear one auth entry
--------------------

:description: Clear one auth entry by entering the ``--name`` of an already
              created entry.
:steps: Run ``rho auth clear --name <name>``
:expectedresults: The auth entry is removed and the ``credentials`` file is
                  updated properly.

Clear multiple auth entries
---------------------------

:description: Clear multiple auth entries using the ``--all`` option.
:steps: Run ``rho auth clear --all``
:expectedresults: All auth entries are removed and the ``credentials`` file is
                  deleted.

Clear one auth entry with vault
-------------------------------

:description: Clear one auth entry by entering the ``--name`` of an already
              created entry and passing the ``--vault`` option.
:steps: Run ``rho auth clear --name <name> --vault <vault>``
:expectedresults: The auth entry is removed and the ``credentials`` file is
                  updated properly.

Clear multiple auth entries with vault
--------------------------------------

:description: Clear multiple auth entries using the ``--all`` option and
              passing the ``--vault`` option.
:steps: Run ``rho auth clear --all --vault <vault>``
:expectedresults: All auth entries are removed and the ``credentials`` file is
                  deleted.

Clear one auth entry (negative)
-------------------------------

:description: Try to clear one invalid auth entry by entering an invalid
              ``--name``.
:steps: Run ``rho auth clear --name <invalidname>``
:expectedresults: The command will fail and the ``credentials`` file is not
                  updated.

Clear one auth entry with vault (negative)
------------------------------------------

:description: Clear one auth entry by entering the ``--name`` of an already
              created entry and passing an invalid value for the ``--vault``
              option.
:steps: Run ``rho auth clear --name <name> --vault <invalidvault>``
:expectedresults: The auth entry is not removed and the ``credentials`` file is
                  not updated.
:bug: https://github.com/quipucords/rho/issues/132

Clear multiple auth entries with vault (negative)
-------------------------------------------------

:description: Clear multiple auth entries using the ``--all`` option and
              passing an invalid value for the ``--vault`` option.
:steps: Run ``rho auth clear --all --vault <invalidvault>``
:expectedresults: All auth entries are not removed and the ``credentials`` file
                  is not deleted.

rho auth edit
=============

Edit auth username
------------------

:description: Edit the username of an auth entry.
:steps: Run ``rho auth edit --name <name> --username <newusername>``
:expectedresults: The auth username must be updated and the ``credentials``
                  file must be updated.

Edit auth password
------------------

:description: Edit the password of an auth entry.
:steps: Run ``rho auth edit --name <name> --password <newpassword>``
:expectedresults: The auth password must be updated and the ``credentials``
                  file must be updated.

Edit auth sshkeyfile
--------------------

:description: Edit the sshkeyfile of an auth entry.
:steps: Run ``rho auth edit --name <name> --sshkeyfile <newsshkeyfile>``
:expectedresults: The auth sshkeyfile must be updated and the ``credentials``
                  file must be updated.

Edit auth username with vault
-----------------------------

:description: Edit the username of an auth entry passing the ``--vault``
              option.
:steps: Run ``rho auth edit --name <name> --username <newusername> --vault
        <vault>``
:expectedresults: The auth username must be updated and the ``credentials``
                  file must be updated.

Edit auth password with vault
-----------------------------

:description: Edit the password of an auth entry passing the ``--vault``
              option.
:steps: Run ``rho auth edit --name <name> --password <newpassword> --vault
        <vault>``
:expectedresults: The auth password must be updated and the ``credentials``
                  file must be updated.

Edit auth sshkeyfile with vault
-------------------------------

:description: Edit the sshkeyfile of an auth entry passing the ``--vault``
              option.
:steps: Run ``rho auth edit --name <name> --sshkeyfile <newsshkeyfile> --vault
        <vault>``
:expectedresults: The auth sshkeyfile must be updated and the ``credentials``
                  file must be updated.

Edit auth username (negative)
-----------------------------

:description: Try to edit the username of a not created auth entry.
:steps: Run ``rho auth edit --name <invalidname> --username <newusername>``
:expectedresults: The command must fail and the ``credentials`` file must not
                  be updated.

Edit auth password (negative)
-----------------------------

:description: Try to edit the password of a not created auth entry.
:steps: Run ``rho auth edit --name <invalidname> --password <newpassword>``
:expectedresults: The command must fail and the ``credentials`` file must not
                  be updated.

Edit auth sshkeyfile (negative)
-------------------------------

:description: Try to edit the sshkeyfile of a not created auth entry.
:steps: Run ``rho auth edit --name <invalidname> --sshkeyfile <newsshkeyfile>``
:expectedresults: The command must fail and the ``credentials`` file must not
                  be updated.

Edit auth vault (negative)
--------------------------

:description: Try to edit the username of an auth entry passing an invalid
              value for the ``--vault`` option.
:steps: Run ``rho auth edit --name <name> --username <newusername> --vault
        <invalidvault>``
:expectedresults: The auth username is not updated and the ``credentials`` file
                  is not updated.

rho auth list
=============

List auth entries
-----------------

:description: List auth entries.
:steps: Run ``rho auth list``.
:expectedresults: All auth entries must be listed.

List auth entries (negative)
----------------------------

:description: Try to list auth entries entering wrong vault password.
:steps: Run ``rho auth list`` and input an invalid vault password.
:expectedresults: The command must fail with a proper error message.
:bug: https://github.com/quipucords/rho/issues/132

List auth entries with vault
----------------------------

:description: List auth entries passing the ``--vault`` option.
:steps: Run ``rho auth list --vault <vault>``.
:expectedresults: All auth entries must be listed.

List auth entries with vault (negative)
---------------------------------------

:description: Try to list auth entries entering an invalid value for the
              ``--vault`` option.
:steps: Run ``rho auth list --vault <invalidvault>``.
:expectedresults: The command must fail with a proper error message.
:bug: https://github.com/quipucords/rho/issues/132

rho auth show
=============

Show an auth entry
------------------

:description: Show an auth entry.
:steps: Run ``rho auth show --name <name>``.
:expectedresults: The auth entry must be printed.

Show an auth entry (negative)
-----------------------------

:description: Try to list an auth entry entering a wrong name.
:steps: Run ``rho auth show --name <invalidname>``.
:expectedresults: The command must fail with a proper error message.

Show an auth entry with vault
-----------------------------

:description: Show an auth entry passing the ``--vault`` option.
:steps: Run ``rho auth show --vault <vault>``.
:expectedresults: The auth entry must be printed.

Show an auth entry with vault (negative)
----------------------------------------

:description: Try to show an auth entry entering an invalid value for the
              ``--vault`` option.
:steps: Run ``rho auth show --vault <invalidvault>``.
:expectedresults: The command must fail with a proper error message.
:bug: https://github.com/quipucords/rho/issues/132

-------
Profile
-------

rho profile add
===============

Add profile with required options
---------------------------------

:description: Add an profile entry providing only the required options
              ``--name``, ``--hosts`` and ``--auth``.
:steps: Run ``rho profile add --name <name> --hosts <hosts> --auth
        <authname>``.
:expectedresults: A new profile entry is created and the data must be
                  the same as the input. Also the entry must be available on
                  the ``profiles`` file.

Add profile with SSH port
-------------------------

:description: Add an profile entry providing the ``--sshport`` in addition to
              the required options.
:steps: Run ``rho profile add --name <name> --hosts <hosts> --auth
        <authname> --sshport <sshport>``.
:expectedresults: A new profile entry is created and data must be the same as the
                  input. Also the entry must be available on the

Add profile with vault
----------------------

:description: Add an profile entry providing the required options ``--name``,
              ``--hosts`` and ``--auth`` passing the ``--vault`` option.
:steps: Run ``rho profile add --name <name> --hosts <hosts> --auth <authname>
        --vault <vault>``.
:expectedresults: A new profile entry is created and the data must be
                  the same as the input. Also the entry must be available on
                  the ``profiles`` file.
                  ``profiles`` file.

Add profile with a duplicated name (negative)
---------------------------------------------

:description: Try to add a profile with the same name of an already created
              one.
:steps:
    * Run ``rho profile add --name <name1> --hosts <hosts> --auth <authname>``.
    * Then run ``rho profile add --name <name1> --hosts <hosts> --auth
      <authname>``.
:expectedresults: The command must fail saying that a profile already exist
                  with that name. Also no entry must be created on the
                  ``profiles`` file.

Add profile with an invalid auth entry (negative)
-------------------------------------------------

:description: Try to add a profile with an auth entry that does not exist.
:steps: Run ``rho profile add --name <name> --hosts <hosts> --auth
        <invalidauthname>``.
:expectedresults: The command must fail saying that the auth entry does not
                  exist. Also no entry must be created on the ``profiles``
                  file.

Add profile with vault (negative)
---------------------------------

:description: Add an profile entry providing the required options ``--name``,
              ``--hosts`` and ``--auth`` passing an invalud value for the
              ``--vault`` option.
:steps: Run ``rho profile add --name <name> --hosts <hosts> --auth <authname>
        --vault <invalidvault>``.
:expectedresults: The command must fail and no profile entry is created. Also
                  the ``profiles`` file is not updated.
:bug: https://github.com/quipucords/rho/issues/132

rho profile clear
=================

Clear one profile entry
-----------------------

:description: Clear one profile entry by entering the ``--name`` of an already
              created entry.
:steps: Run ``rho profile clear --name <name>``
:expectedresults: The profile entry is removed and the ``profiles`` file is
                  updated properly.

Clear multiple profile entries
------------------------------

:description: Clear multiple profile entries using the ``--all`` option.
:steps: Run ``rho profile clear --all``
:expectedresults: All profile entries are removed and the ``profiles`` file is
                  deleted.

Clear one profile entry with vault
----------------------------------

:description: Clear one profile entry by entering the ``--name`` of an already
              created entry and passing the ``--vault`` option.
:steps: Run ``rho profile clear --name <name> --vault <vault>``
:expectedresults: The profile entry is removed and the ``profiles`` file is
                  updated properly.

Clear multiple profile entries with vault
-----------------------------------------

:description: Clear multiple profile entries using the ``--all`` option and
              passing the ``--vault`` option.
:steps: Run ``rho profile clear --all --vault <vault>``
:expectedresults: All profile entries are removed and the ``profiles`` file is
                  deleted.

Clear one profile entry (negative)
----------------------------------

:description: Try to clear one invalid profile entry by entering an invalid
              ``--name``.
:steps: Run ``rho profile clear --name <invalidname>``
:expectedresults: The command will fail and the ``profiles`` file is not
                  updated.

Clear one profile entry with vault (negative)
---------------------------------------------

:description: Clear one profile entry by entering the ``--name`` of an already
              created entry and passing an invalid value for the ``--vault``
              option.
:steps: Run ``rho profile clear --name <name> --vault <invalidvault>``
:expectedresults: The profile entry is not removed and the ``profiles`` file is
                  not updated.
:bug: https://github.com/quipucords/rho/issues/132

Clear multiple profile entries with vault (negative)
----------------------------------------------------

:description: Clear multiple profile entries using the ``--all`` option and
              passing an invalid value for the ``--vault`` option.
:steps: Run ``rho profile clear --all --vault <invalidvault>``
:expectedresults: All profile entries are not removed and the ``profiles`` file
                  is not deleted.
:bug: https://github.com/quipucords/rho/issues/132

rho profile edit
================

Edit profile hosts
------------------

:description: Edit the hosts of an profile entry.
:steps: Run ``rho profile edit --name <name> --hosts <newhosts>``
:expectedresults: The profile hosts must be updated and the ``profiles``
                  file must be updated.

Edit profile sshport
--------------------

:description: Edit the sshport of an profile entry.
:steps: Run ``rho profile edit --name <name> --sshport <newsshport>``
:expectedresults: The profile sshport must be updated and the ``profiles``
                  file must be updated.

Edit profile auth
-----------------

:description: Edit the auth of an profile entry.
:steps: Run ``rho profile edit --name <name> --auth <newauth>``
:expectedresults: The profile auth must be updated and the ``profiles``
                  file must be updated.

Edit profile hosts with vault
-----------------------------

:description: Edit the hosts of an profile entry passing the ``--vault``
              option.
:steps: Run ``rho profile edit --name <name> --hosts <newhosts> --vault
        <vault>``
:expectedresults: The profile hosts must be updated and the ``profiles``
                  file must be updated.

Edit profile sshport with vault
-------------------------------

:description: Edit the sshport of an profile entry passing the ``--vault``
              option.
:steps: Run ``rho profile edit --name <name> --sshport <newsshport> --vault
        <vault>``
:expectedresults: The profile sshport must be updated and the ``profiles``
                  file must be updated.

Edit profile auth with vault
----------------------------

:description: Edit the auth of an profile entry passing the ``--vault``
              option.
:steps: Run ``rho profile edit --name <name> --auth <newauth> --vault
        <vault>``
:expectedresults: The profile auth must be updated and the ``profiles``
                  file must be updated.

Edit profile hosts (negative)
-----------------------------

:description: Try to edit the hosts of a not created profile entry.
:steps: Run ``rho profile edit --name <invalidname> --hosts <newhosts>``
:expectedresults: The command must fail and the ``profiles`` file must not be
                  updated.

Edit profile sshport (negative)
-------------------------------

:description: Try to edit the sshport of a not created profile entry.
:steps: Run ``rho profile edit --name <invalidname> --sshport <newsshport>``
:expectedresults: The command must fail and the ``profiles`` file must not be
                  updated.

Edit profile auth (negative)
----------------------------

:description: Try to edit the auth of a not created profile entry.
:steps: Run ``rho profile edit --name <invalidname> --auth <newauth>``
:expectedresults: The command must fail and the ``profiles`` file must not be
                  updated.

Edit profile vault (negative)
-----------------------------

:description: Try to edit the hosts of an profile entry passing an invalid
              value for the ``--vault`` option.
:steps: Run ``rho profile edit --name <name> --hosts <newhosts> --vault
        <invalidvault>``
:expectedresults: The profile hosts is not updated and the ``profiles`` file is
                  not updated.

rho profile list
================

List profile entries
--------------------

:description: List profile entries.
:steps: Run ``rho profile list``.
:expectedresults: All profile entries must be listed.

List profile entries (negative)
-------------------------------

:description: Try to list profile entries entering wrong vault password.
:steps: Run ``rho profile list`` and input an invalid vault password.
:expectedresults: The command must fail with a proper error message.
:bug: https://github.com/quipucords/rho/issues/132

List profile entries with vault
-------------------------------

:description: List profile entries passing the ``--vault`` option.
:steps: Run ``rho profile list --vault <vault>``.
:expectedresults: All profile entries must be listed.

List profile entries with vault (negative)
------------------------------------------

:description: Try to list profile entries entering an invalid value for the
              ``--vault`` option.
:steps: Run ``rho profile list --vault <invalidvault>``.
:expectedresults: The command must fail with a proper error message.
:bug: https://github.com/quipucords/rho/issues/132

rho profile show
================

Show a profile entry
--------------------

:description: Show a profile entry.
:steps: Run ``rho profile show --name <name>``.
:expectedresults: The profile entry must be printed.

Show a profile entry (negative)
-------------------------------

:description: Try to list a profile entry entering wrong name.
:steps: Run ``rho profile show --name <invalidname>``.
:expectedresults: The command must fail with a proper error message.

Show a profile entry with vault
-------------------------------

:description: Show a profile entry passing the ``--vault`` option.
:steps: Run ``rho profile show --vault <vault>``.
:expectedresults: The profile entry must be printed.

Show a profile entry with vault (negative)
------------------------------------------

:description: Try to show a profile entry entering an invalid value for the
              ``--vault`` option.
:steps: Run ``rho profile show --vault <invalidvault>``.
:expectedresults: The command must fail with a proper error message.
:bug: https://github.com/quipucords/rho/issues/132

----
Scan
----

rho scan
========

Scan with --reset on a new profile
----------------------------------

:description: Run scan with the ``--reset`` option on a brand new profile.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts default``.
:expectedresults: The scan must succeed and the ``<reportfile>`` must be
                  created.
:permutations: This test must scan at least a RHEL7 and a CentOS 7 machines.
    More permutations will be added as more Operating Systems and products are
    available.

Scan with facts subset
----------------------

:description: Run scan providing the ``--facts`` option with a facts subset to
              gather.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts <factssubset>``.
:expectedresults: The scan must succeed and the ``<reportfile>`` must be
                  created. Also only the facts subset must be available on the
                  ``<reportfile>``.

Scan with ansible_forks
-----------------------

:description: Run scan providing the ``--ansible_forks`` option.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts default --ansible_forks <num_forks>``.
:expectedresults: The scan must succeed and the ``<reportfile>`` must be
                  created. The output must provide how many forks were used and
                  it must be equal to the ``<num_forks>``.

Scan with vault
---------------

:description: Run scan providing the ``--vault`` option.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts default --vault <vault>``.
:expectedresults: The scan must succeed and the ``<reportfile>`` must be
                  created.

Scan without --reset on a new profile
-------------------------------------

:description: Try to run scan without the ``--reset`` option on a brand new
              profile.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reportfile <reportfile> --profile <profile> --facts
       default``.
:expectedresults: The command must fail stating that the profile has not been
                  processed and the ``--reset`` option must be used when
                  running the profile for the first time.

Scan with --reset on an already processed  profile
--------------------------------------------------

:description: Run scan with the ``--reset`` option on an already processed
              profile.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts default``.
    4. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts default``.
:expectedresults: The scan must succeed and the ``<reportfile>`` must be
                  created.

Scan with invalid profile (negative)
------------------------------------

:description: Run scan providing an invalid value for the ``--profile`` option.
:steps: Run ``rho scan --reset --reportfile <reportfile> --profile
        <invalidprofile> --facts default``.
:expectedresults: The command must fail stating that the profile value is
                  invalid.

Scan with invalid facts (negative)
----------------------------------

:description: Run scan providing an invalid value for the ``--facts`` option.
:steps: Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
        --facts <invalidfacts>``.
:expectedresults: The command must fail stating that the facts value is
                  invalid.

Scan with invalid ansible_forks (negative)
------------------------------------------

:description: Run scan providing an invalid value for the ``--ansible_forks``
              option.
:steps: Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
        --facts default --ansible_forks <invalidansible_forks>``.
:expectedresults: The command must fail stating that the ansible_forks value is
                  invalid.

Scan with vault (negative)
--------------------------

:description: Run scan providing an invalid value for the ``--vault`` option.
:steps:
    1. Create an auth
    2. Create a profile and link to the auth on step 1
    3. Run ``rho scan --reset --reportfile <reportfile> --profile <profile>
       --facts default --vault <invalidvault>``.
:expectedresults: The scan must not happen and the ``<reportfile>`` must not be
                  created.
:bug: https://github.com/quipucords/rho/issues/132

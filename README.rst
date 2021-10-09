Timewarrior Balance
###################

.. contents::

.. sectnum::

Introduction
============

This is a timewarrior_ extension for generating a report providing a balance
between hours your worked and hours you have planned to work. This primarily
is intended for users that have a flexible work hours regime and want to keep
track of the balance between allotted time (hours to worked) and time actually
spent (worked hours).

Below is an example of a call to the extension::

  $ timew bal :week
  Start: Mon Oct  4 00:00:00 2021
    End: Mon Oct 11 00:00:00 2021

    Tag  Spent  Allotted  Balance
  ───────────────────────────────
   work  36:57     40:00    -4:03
  study  11:00     10:00    +1:00
  ───────────────────────────────
  TOTAL  47:58     50:00    -3:02


And below is the content of the configuration file for such example::

  # Hours for the "work" tag
  work {
    # Periodic configuration
    from 2021-10-01 {
      mon  11:00
      tue   9:00
      wed   5:30
      thu   6:30
      fri   8:00
    }

    # Individual entries for adjustment
    2021-10-01  8:00 "Adjustment"
    2021-10-12 -8:00 "National holiday"
  }

  # Hours for the "study" tag
  study {
    from 2021-10-01 {
      mon 2:00
      tue 2:00
      wed 2:00
      thu 2:00
      fri 2:00
    }
  }


Install
=======

Using the source directly
-------------------------

There are no extra dependencies besides Python 3 for running this extension.
As such, you can just add a script in your timewarrior extensions directory
(usually ``~/.timewarrior/extensions/``) that just runs
`<timewarrior_balance/balance.py>`_.

If you are on a regular Unix machine, we provide a wrapper script
(`<balance.sh>`_) that can be simply be symlinked::

  $ ln -s $(realpath balance.sh) ~/.timewarrior/extensions/balance

Using pip
---------

You can also install the package with ``pip`` and add a script in the
extensions directory to call ``python -m timewarrior_balance``::

  $ pip install --user timewarrior-balance
  $ echo "python -m timewarrior_balance" > ~/.timewarrior/extensions/balance
  $ chmod a+x ~/.timewarrior/extensions/balance


Usage
=====

Calling the extension
---------------------

Considering that the extension is installed in timewarrior's extension
directory as a script named ``balance`` and that you have already provided a
`configuration file`_, it is possible to call the
extension to generate the report by calling ``timew balance``. It is also
convenient to use the abbreviated form ``timew bal`` for cases when there are
no conflict with other installed extensions::

  $ timew bal
  Start: Tue Jan  2 00:00:00 0001
    End: Mon Oct 11 07:22:47 2021

    Tag  Spent  Allotted  Balance
  ───────────────────────────────
   work  48:30     56:00    -8:30
  study  11:00     12:00    -1:00
  ───────────────────────────────
  TOTAL  59:30     68:00    -9:30

The report will count how much time is allotted and how much has been spent
for each configured tag in the interval of the report. The extension uses the
interval the user provided to the ``timew`` command (which is parsed directly
by ``timewarrior`` itself). If no period is passed, like in the case above,
then it will default to be from ``0001-01-02`` until (exclusively) the
date-time for when the report was called.

Bellow is an example of a report for the current week::

  $ timew bal :week
  Start: Mon Oct 11 00:00:00 2021
    End: Mon Oct 18 00:00:00 2021

    Tag  Spent  Allotted  Balance
  ───────────────────────────────
   work   4:30     32:00   -27:30
  study   1:00     10:00    -9:00
  ───────────────────────────────
  TOTAL   5:30     42:00   -36:30

It shows that I still have to spend 27.5 hours and 9 hours on work and
studies, respectively (let's hope this is the beginning of the week 😛).

We can also use dates explicitly. Below is the same report using dates::

  $ timew bal 2021-10-11 to 2021-10-18
  Start: Mon Oct 11 00:00:00 2021
    End: Mon Oct 18 00:00:00 2021

    Tag  Spent  Allotted  Balance
  ───────────────────────────────
   work   4:30     32:00   -27:30
  study   1:00     10:00    -9:00
  ───────────────────────────────
  TOTAL   5:30     42:00   -36:30

As said before, the interval used by the report is parsed by timewarrior, so
you can use anything that is recognized by timewarrior.

Configuration file
------------------
.. _`configuration file`:

In order to use this extension, you need to create a configuration file named
``balance.conf`` and place it under your timewarrior data directory (usually
``~/.timewarrior/``). This configuration file is were you declare the hours
you need to spend on your activities.

The configuration file is composed by a series of blocks, where each block is
a configuration for a tag you want to track. The example below shows the
content a configuration file with two empty blocks::

  # Everything from the "#" to the end of line is considered to be a comment

  work {
    # This is an example of a configuration block to tracking hours for the
    # "work" tag
  }

  "tag with multiple words" {
    # You can use double quotes for tags with multiple words
  }

A block has the form ``<tag> { <content> }``, that is, it is defined with the
name of the tag you want to track followed by the content embraced by a pair
of opening and closing braces.

- ``<tag>`` can be a single word as the tag name or a string enclosed by
  double-quotes, which is useful when the tag name contains spaces or is one
  of the reserved keywords of balance's configuration file. You can also use
  the token ``__untagged__`` in order to provide configuration for untagged
  timewarrior records.

- ``<content>`` contains the configuration for the referred tag and may have
  two types of things:

  1. **Pediodic blocks**, where you can define the time allotted for each
     day of the week;

  2. Individual **date entries**, which specify allotted times for a specific
     day.


Periodic Blocks
'''''''''''''''

Below are some examples of periodic blocks::

  "study music" {
    from 2021-10-02 {
      # I'll dedicate 1 and 2½ hours to study music on Mondays and
      # Wednesdays, respectively
      mon 1:00
      wed 2:30
    }

    # I will dedicate a little more time to the activity in December
    from 2021-12-01 to 2022-01-01 {
      mon 1:00
      wed 2:30
      fri 2:00
    }
  }

  work {
    # Part-time job
    from 2021-01-01 {
      mon 5:00
      tue 4:00
      wed 6:00
      thu 5:00
    }

    # Got a full-time job in April
    from 2021-04-15 {
      mon 8:00
      tue 8:00
      wed 8:00
      thu 8:00
      fri 8:00
    }
  }

When calculating the amount of allotted time for each tag, based on the
report's start and end date, the extension calculates the number of matches
possible for each rule and adds the expected time.

Below is a more formal-like description of the format.

- A periodic block has the form ``from <start-date> [to <end-date>] {
  <rules> }``.

- ``<start-date>`` and ``<end-date>`` define the time interval for which
  the rules defined in ``<rules>`` have effect. The format of a date is
  ``YYYY-MM-DD``, defining the year, month and day, respectively.  Note
  that the interval is inclusive on ``<start-date>`` and exclusive on
  ``<end-date>``.

  The end date is optional. If omitted, it defaults to *(i)* the start date
  of the next periodic block or *(ii)* the end date of the report if this
  is the last periodic block of the tag block. You can use ``end of time``
  in order to explicitly have the effect of the latter (useful when the
  periodic block is not the last one).

- ``<rules>`` is a list of pairs in the format ``<weekday> <hours>``,
  representing the amount of time allotted for days of the week.

  - ``<weekday>`` must be one of: ``mon``, ``tue``, ``wed``, ``thu``,
    ``fri``, ``sat`` and ``sun``.

  - ``<hours>`` is defined by a number of hours optionally followed by
    ``:`` and a number of minutes. Examples: ``5``, ``2:15``, ``7:00``.


Date entries
''''''''''''

Besides describing periodic rules for allotted time, it is also possible
to specify allotted time for specific date via **date entries**. This is
specially useful to make exceptions to the rules (e.g. holidays).

A date entry have a very simple format: ``<date> <hours> [<note>]``:

- ``<date>`` is a date in the format ``YYYY-MM-DD``.

- ``<hours>`` is in the same format as for hours in the rules of periodic
  blocks. The value of ``<hours>`` does not replace the allotted time for the
  day. Instead, it might be a positive or negative value, adding to or
  subtracting from the time for the day.

- ``<note>`` is an optional string enclosed by double-quotes that describes
  the entry.

Below are some examples of uses of date entries::

  work {
    from 2021-10-01 {
      mon  11:00
      tue   9:00
      wed   5:30
      thu   6:30
      fri   8:00
    }

    2021-10-12 -8:00 "National holiday"
    2021-12-15 +2:00 "Extra hours for this specific day"

    # Note that the plus char is optional
    2021-12-24  2:00
  }


License
=======

This extension is released under `Mozilla Public License 2.0`_. A copy of the
license is provided in `<LICENSE.txt>`_.


.. Links
.. _`Mozilla Public License 2.0`: https://www.mozilla.org/en-US/MPL/2.0/
.. _timewarrior: https://timewarrior.net/

.. include:: aliases.rst

.. _troubleshooting:

===============
Troubleshooting
===============

So you've installed Congress with devstack as per the README,
and now something is not behaving the way you think it should.
Let's say you're using the policy that follows (from the tutorial),
but the *error* table does not contain the rows you expect.  In
this document, we describe how to figure out what the problem is
and hopefully how to fix it.  At the end we also detail a collection
of problems and tips for how to fix them.  ::

    error(name2) :-
      neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p),
      nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2),
      neutron:networks(a3, b3, c3, d3, e3, f3, tenant_id3, h3, i3, j3, network_id, l3),
      not same_group(tenant_id, tenant_id2)

    error(name2) :-
      neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p),
      nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2),
      neutron:networks(a3, b3, c3, d3, e3, f3, tenant_id3, h3, i3, j3, network_id, l3),
      not same_group(tenant_id2, tenant_id3)

    same_group(x, y) :-
        group(x, g),
        group(y, g)

  group("7320f8345acb489e8296ddb3b1ad1262", "IT") :- true()
  group("81084a94769c4ce0accb6968c397a085", "Marketing") :- true()


Policy-engine troubleshooting
-----------------------------

Make sure the policy engine knows about the rules you think it knows about.
It is possible that the policy engine rejected a rule because of a syntax
error.  Let's assume you're using the *classification* policy.


**Check**: Ensure the policy engine has the right rules::

  $ curl -X GET localhost:1789/v1/policies/<classification-id>/rules

For example::

  $ curl -X GET localhost:1789/v1/policies/<classification-id>/rules
  {
    "results": [
      {
        "comment": "None",
        "id": "2be98841-953d-44f0-91f6-32c5f4dd4f83",
        "rule": "group(\"d0a7ff9e5d5b4130a586a7af1c855c3e\", \"IT\") :- true()"
      },
      {
        "comment": "None",
        "id": "c01067ef-10e4-498f-8aaa-0c1cce1272a3",
        "rule": "group(\"e793326db18847e1908e791daa69a5a3\", \"Marketing\") :- true()"
      },
      {
        "comment": "None",
        "id": "3c6e48ee-2783-4b5e-94ff-aab00ccffd42",
        "rule": "error(name2) :- neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p), nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2), neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, network_id, i3), not same_group(tenant_id, tenant_id2)"
      },
      {
        "comment": "None",
        "id": "36264def-d917-4f39-a6b0-4aaf12d4b349",
        "rule": "error(name2) :- neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p), nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2), neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, network_id, i3), not same_group(tenant_id2, tenant_id3)"
      },
      {
        "comment": "None",
        "id": "31922bb0-711c-43da-9f11-cef69828a2c4",
        "rule": "same_group(x, y) :- group(x, g), group(y, g)"
      }
    ]
  }

It is also possible that you might have a typo in one of the table names that appear
in the rules.  To eliminate that possibility, ask the list of tables
that occur in the rules and compare those to the ones the datasources export.
You might also look for near-duplicates, such as *same_group* and *samegroup*,
in case tables are spelled differently in different rules.

**Check**: Ensure there are no typos in any of the table names by asking
for the list of tables occurring in the rules::

  $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables

For example::

  $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables
  {
    "results": [
      {
        "id": "nova:servers"
      },
      {
        "id": "neutron:ports"
      },
      {
        "id": "group"
      },
      {
        "id": "neutron:networks"
      },
      {
        "id": "error"
      },
      {
        "id": "same_group"
      },
      {
        "id": "true"
      }
    ]
  }

Next we want to check that tables have the rows we would expect.  A good place
to start is with the tables exported by external datasources like Nova and
Neutron.  If these tables are empty, that points to a problem with the
datasources (see below for troubleshooting datasources).
If they are not empty, it points to a problem with the rules::

   $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables/<table-id>/rows

For example, below are the rows in the *neutron:ports* table.  There are 2
rows (each of which represents a port), and each row has 16 columns::

   $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables/neutron:ports/rows
  {
    "results": [
      {
        "data": [
          "795a4e6f-7cc8-4052-ae43-80d4c3ad233a",
          "5f1f9b53-46b2-480f-b653-606f4aaf61fd",
          "1955273c-242d-46a6-8063-7dc9c20cbba9",
          "None",
          "ACTIVE",
          "",
          "True",
          "37eee894-a65f-414d-bd8c-a9363293000a",
          "e793326db18847e1908e791daa69a5a3",
          "None",
          "network:router_interface",
          "fa:16:3e:28:ab:0b",
          "4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c",
          "882911e9-e3cf-4682-bb18-4bf8c559e22d",
          "c62efe5d-d070-4dff-8d9d-3df8ac08b0ec",
          "None"
        ]
      },
      {
        "data": [
          "ebeb4ee6-14be-4ba2-a723-fd62f220b6b9",
          "f999de49-753e-40c9-9eed-d01ad76bc6c3",
          "ad058c04-05be-4f56-a76f-7f3b42f36f79",
          "None",
          "ACTIVE",
          "",
          "True",
          "07ecce19-d7a4-4c79-924e-1692713e53a7",
          "e793326db18847e1908e791daa69a5a3",
          "None",
          "compute:None",
          "fa:16:3e:3c:0d:13",
          "af179309-65f7-4662-a087-e583d6a8bc21",
          "149f4271-41ca-4b1a-875b-77909debbeac",
          "bc333f0f-b665-4e2b-97db-a4dd985cb5c8",
          "None"
        ]
      }
    ]
  }

After checking the tables exported by datasources like Nova and Neutron,
it is useful to check the contents of the other tables that build upon
those tables.

In our running example, we should check the rows of the *group* table.  Here
we see what we expect: that there are two users, each of which belongs to
a different group::

    $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables/group/rows
    {
      "results": [
        {
          "data": [
            "d0a7ff9e5d5b4130a586a7af1c855c3e",
            "IT"
          ]
        },
        {
          "data": [
            "e793326db18847e1908e791daa69a5a3",
            "Marketing"
          ]
        }
      ]
    }

Once you have found a table that contains the wrong rows, it may be obvious
looking at the rules for that table what the problem is.  But if there
are many rules or if some of the rules are long, it can be difficult to
pinpoint the problem.  When this happens, you can ask for a trace that
describes how the rows of that table were computed::

   $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables/<table-id>/rows?trace=true

The trace is similar to a function-call trace. It uses the following
annotations::

* Call Q: a query for all the rows that match Q
* Exit Q: successfully discovered row Q
* Fail Q: failure to find a row matching Q (in the current context)
* Redo Q: attempt to find another row matching Q

In our example, we know the contents of the *error* table is empty, but
all of the tables used to construct *error* look reasonable.  So we ask
for a trace showing why the *error* table is empty.  The trace is returned
as a string and be quite large.::

  $ curl -X GET localhost:1789/v1/policies/<classification-id>/tables/error/rows?trace=true
  {
    "results": [],
    "trace": "Clas  : Call: error(x0)\nClas  : | Call: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)\nClas  : | Exit: neutron:ports(\"795a4e6f-7cc8-4052-ae43-80d4c3ad233a\", \"5f1f9b53-46b2-480f-b653-606f4aaf61fd\", \"1955273c-242d-46a6-8063-7dc9c20cbba9\", \"None\", \"ACTIVE\", \"\", \"True\", \"37eee894-a65f-414d-bd8c-a9363293000a\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"network:router_interface\", \"fa:16:3e:28:ab:0b\", \"4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c\", \"882911e9-e3cf-4682-bb18-4bf8c559e22d\", \"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", \"None\")\nClas  : | Call: nova:servers(\"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Fail: nova:servers(\"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Redo: neutron:ports(\"795a4e6f-7cc8-4052-ae43-80d4c3ad233a\", \"5f1f9b53-46b2-480f-b653-606f4aaf61fd\", \"1955273c-242d-46a6-8063-7dc9c20cbba9\", \"None\", \"ACTIVE\", \"\", \"True\", \"37eee894-a65f-414d-bd8c-a9363293000a\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"network:router_interface\", \"fa:16:3e:28:ab:0b\", \"4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c\", \"882911e9-e3cf-4682-bb18-4bf8c559e22d\", \"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", \"None\")\nClas  : | Exit: neutron:ports(\"ebeb4ee6-14be-4ba2-a723-fd62f220b6b9\", \"f999de49-753e-40c9-9eed-d01ad76bc6c3\", \"ad058c04-05be-4f56-a76f-7f3b42f36f79\", \"None\", \"ACTIVE\", \"\", \"True\", \"07ecce19-d7a4-4c79-924e-1692713e53a7\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"compute:None\", \"fa:16:3e:3c:0d:13\", \"af179309-65f7-4662-a087-e583d6a8bc21\", \"149f4271-41ca-4b1a-875b-77909debbeac\", \"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"None\")\nClas  : | Call: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Exit: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"vm-demo\", \"c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d\", \"ACTIVE\", \"e793326db18847e1908e791daa69a5a3\", \"cf23fabed97742a9af463002e68068bd\", \"6183d5a6-e26c-4f48-af4d-5d0b6770a976\", \"1\")\nClas  : | Call: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, \"07ecce19-d7a4-4c79-924e-1692713e53a7\", i3)\nClas  : | Fail: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, \"07ecce19-d7a4-4c79-924e-1692713e53a7\", i3)\nClas  : | Redo: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"vm-demo\", \"c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d\", \"ACTIVE\", \"e793326db18847e1908e791daa69a5a3\", \"cf23fabed97742a9af463002e68068bd\", \"6183d5a6-e26c-4f48-af4d-5d0b6770a976\", \"1\")\nClas  : | Fail: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Redo: neutron:ports(\"ebeb4ee6-14be-4ba2-a723-fd62f220b6b9\", \"f999de49-753e-40c9-9eed-d01ad76bc6c3\", \"ad058c04-05be-4f56-a76f-7f3b42f36f79\", \"None\", \"ACTIVE\", \"\", \"True\", \"07ecce19-d7a4-4c79-924e-1692713e53a7\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"compute:None\", \"fa:16:3e:3c:0d:13\", \"af179309-65f7-4662-a087-e583d6a8bc21\", \"149f4271-41ca-4b1a-875b-77909debbeac\", \"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"None\")\nClas  : | Fail: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)\nClas  : | Call: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)\nClas  : | Exit: neutron:ports(\"795a4e6f-7cc8-4052-ae43-80d4c3ad233a\", \"5f1f9b53-46b2-480f-b653-606f4aaf61fd\", \"1955273c-242d-46a6-8063-7dc9c20cbba9\", \"None\", \"ACTIVE\", \"\", \"True\", \"37eee894-a65f-414d-bd8c-a9363293000a\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"network:router_interface\", \"fa:16:3e:28:ab:0b\", \"4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c\", \"882911e9-e3cf-4682-bb18-4bf8c559e22d\", \"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", \"None\")\nClas  : | Call: nova:servers(\"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Fail: nova:servers(\"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Redo: neutron:ports(\"795a4e6f-7cc8-4052-ae43-80d4c3ad233a\", \"5f1f9b53-46b2-480f-b653-606f4aaf61fd\", \"1955273c-242d-46a6-8063-7dc9c20cbba9\", \"None\", \"ACTIVE\", \"\", \"True\", \"37eee894-a65f-414d-bd8c-a9363293000a\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"network:router_interface\", \"fa:16:3e:28:ab:0b\", \"4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c\", \"882911e9-e3cf-4682-bb18-4bf8c559e22d\", \"c62efe5d-d070-4dff-8d9d-3df8ac08b0ec\", \"None\")\nClas  : | Exit: neutron:ports(\"ebeb4ee6-14be-4ba2-a723-fd62f220b6b9\", \"f999de49-753e-40c9-9eed-d01ad76bc6c3\", \"ad058c04-05be-4f56-a76f-7f3b42f36f79\", \"None\", \"ACTIVE\", \"\", \"True\", \"07ecce19-d7a4-4c79-924e-1692713e53a7\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"compute:None\", \"fa:16:3e:3c:0d:13\", \"af179309-65f7-4662-a087-e583d6a8bc21\", \"149f4271-41ca-4b1a-875b-77909debbeac\", \"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"None\")\nClas  : | Call: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Exit: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"vm-demo\", \"c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d\", \"ACTIVE\", \"e793326db18847e1908e791daa69a5a3\", \"cf23fabed97742a9af463002e68068bd\", \"6183d5a6-e26c-4f48-af4d-5d0b6770a976\", \"1\")\nClas  : | Call: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, \"07ecce19-d7a4-4c79-924e-1692713e53a7\", i3)\nClas  : | Fail: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, \"07ecce19-d7a4-4c79-924e-1692713e53a7\", i3)\nClas  : | Redo: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"vm-demo\", \"c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d\", \"ACTIVE\", \"e793326db18847e1908e791daa69a5a3\", \"cf23fabed97742a9af463002e68068bd\", \"6183d5a6-e26c-4f48-af4d-5d0b6770a976\", \"1\")\nClas  : | Fail: nova:servers(\"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", x0, c2, d2, tenant_id2, f2, g2, h2)\nClas  : | Redo: neutron:ports(\"ebeb4ee6-14be-4ba2-a723-fd62f220b6b9\", \"f999de49-753e-40c9-9eed-d01ad76bc6c3\", \"ad058c04-05be-4f56-a76f-7f3b42f36f79\", \"None\", \"ACTIVE\", \"\", \"True\", \"07ecce19-d7a4-4c79-924e-1692713e53a7\", \"e793326db18847e1908e791daa69a5a3\", \"None\", \"compute:None\", \"fa:16:3e:3c:0d:13\", \"af179309-65f7-4662-a087-e583d6a8bc21\", \"149f4271-41ca-4b1a-875b-77909debbeac\", \"bc333f0f-b665-4e2b-97db-a4dd985cb5c8\", \"None\")\nClas  : | Fail: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)\nClas  : Fail: error(x0)\n"
  }

We can print the trace using 'printf <trace>' (without the quotes)::

  $ printf "Clas  : Call: error(x0)...
  Clas  : Call: error(x0)
  Clas  : | Call: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)
  Clas  : | Exit: neutron:ports("795a4e6f-7cc8-4052-ae43-80d4c3ad233a", "5f1f9b53-46b2-480f-b653-606f4aaf61fd", "1955273c-242d-46a6-8063-7dc9c20cbba9", "None", "ACTIVE", "", "True", "37eee894-a65f-414d-bd8c-a9363293000a", "e793326db18847e1908e791daa69a5a3", "None", "network:router_interface", "fa:16:3e:28:ab:0b", "4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c", "882911e9-e3cf-4682-bb18-4bf8c559e22d", "c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", "None")
  Clas  : | Call: nova:servers("c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Fail: nova:servers("c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Redo: neutron:ports("795a4e6f-7cc8-4052-ae43-80d4c3ad233a", "5f1f9b53-46b2-480f-b653-606f4aaf61fd", "1955273c-242d-46a6-8063-7dc9c20cbba9", "None", "ACTIVE", "", "True", "37eee894-a65f-414d-bd8c-a9363293000a", "e793326db18847e1908e791daa69a5a3", "None", "network:router_interface", "fa:16:3e:28:ab:0b", "4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c", "882911e9-e3cf-4682-bb18-4bf8c559e22d", "c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", "None")
  Clas  : | Exit: neutron:ports("ebeb4ee6-14be-4ba2-a723-fd62f220b6b9", "f999de49-753e-40c9-9eed-d01ad76bc6c3", "ad058c04-05be-4f56-a76f-7f3b42f36f79", "None", "ACTIVE", "", "True", "07ecce19-d7a4-4c79-924e-1692713e53a7", "e793326db18847e1908e791daa69a5a3", "None", "compute:None", "fa:16:3e:3c:0d:13", "af179309-65f7-4662-a087-e583d6a8bc21", "149f4271-41ca-4b1a-875b-77909debbeac", "bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "None")
  Clas  : | Call: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Exit: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "vm-demo", "c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d", "ACTIVE", "e793326db18847e1908e791daa69a5a3", "cf23fabed97742a9af463002e68068bd", "6183d5a6-e26c-4f48-af4d-5d0b6770a976", "1")
  Clas  : | Call: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, "07ecce19-d7a4-4c79-924e-1692713e53a7", i3)
  Clas  : | Fail: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, "07ecce19-d7a4-4c79-924e-1692713e53a7", i3)
  Clas  : | Redo: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "vm-demo", "c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d", "ACTIVE", "e793326db18847e1908e791daa69a5a3", "cf23fabed97742a9af463002e68068bd", "6183d5a6-e26c-4f48-af4d-5d0b6770a976", "1")
  Clas  : | Fail: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Redo: neutron:ports("ebeb4ee6-14be-4ba2-a723-fd62f220b6b9", "f999de49-753e-40c9-9eed-d01ad76bc6c3", "ad058c04-05be-4f56-a76f-7f3b42f36f79", "None", "ACTIVE", "", "True", "07ecce19-d7a4-4c79-924e-1692713e53a7", "e793326db18847e1908e791daa69a5a3", "None", "compute:None", "fa:16:3e:3c:0d:13", "af179309-65f7-4662-a087-e583d6a8bc21", "149f4271-41ca-4b1a-875b-77909debbeac", "bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "None")
  Clas  : | Fail: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)

  Clas  : | Call: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)
  Clas  : | Exit: neutron:ports("795a4e6f-7cc8-4052-ae43-80d4c3ad233a", "5f1f9b53-46b2-480f-b653-606f4aaf61fd", "1955273c-242d-46a6-8063-7dc9c20cbba9", "None", "ACTIVE", "", "True", "37eee894-a65f-414d-bd8c-a9363293000a", "e793326db18847e1908e791daa69a5a3", "None", "network:router_interface", "fa:16:3e:28:ab:0b", "4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c", "882911e9-e3cf-4682-bb18-4bf8c559e22d", "c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", "None")
  Clas  : | Call: nova:servers("c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Fail: nova:servers("c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Redo: neutron:ports("795a4e6f-7cc8-4052-ae43-80d4c3ad233a", "5f1f9b53-46b2-480f-b653-606f4aaf61fd", "1955273c-242d-46a6-8063-7dc9c20cbba9", "None", "ACTIVE", "", "True", "37eee894-a65f-414d-bd8c-a9363293000a", "e793326db18847e1908e791daa69a5a3", "None", "network:router_interface", "fa:16:3e:28:ab:0b", "4b7e5f9c-9ba8-4c94-a7d0-e5811207d26c", "882911e9-e3cf-4682-bb18-4bf8c559e22d", "c62efe5d-d070-4dff-8d9d-3df8ac08b0ec", "None")
  Clas  : | Exit: neutron:ports("ebeb4ee6-14be-4ba2-a723-fd62f220b6b9", "f999de49-753e-40c9-9eed-d01ad76bc6c3", "ad058c04-05be-4f56-a76f-7f3b42f36f79", "None", "ACTIVE", "", "True", "07ecce19-d7a4-4c79-924e-1692713e53a7", "e793326db18847e1908e791daa69a5a3", "None", "compute:None", "fa:16:3e:3c:0d:13", "af179309-65f7-4662-a087-e583d6a8bc21", "149f4271-41ca-4b1a-875b-77909debbeac", "bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "None")
  Clas  : | Call: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Exit: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "vm-demo", "c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d", "ACTIVE", "e793326db18847e1908e791daa69a5a3", "cf23fabed97742a9af463002e68068bd", "6183d5a6-e26c-4f48-af4d-5d0b6770a976", "1")
  Clas  : | Call: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, "07ecce19-d7a4-4c79-924e-1692713e53a7", i3)
  Clas  : | Fail: neutron:networks(a3, b3, c3, d3, e3, tenant_id3, f3, g3, h3, "07ecce19-d7a4-4c79-924e-1692713e53a7", i3)
  Clas  : | Redo: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "vm-demo", "c5dd62237226c4f2eaddea823ca8b4f5c1a3c2d3a27e5e51e407954d", "ACTIVE", "e793326db18847e1908e791daa69a5a3", "cf23fabed97742a9af463002e68068bd", "6183d5a6-e26c-4f48-af4d-5d0b6770a976", "1")
  Clas  : | Fail: nova:servers("bc333f0f-b665-4e2b-97db-a4dd985cb5c8", x0, c2, d2, tenant_id2, f2, g2, h2)
  Clas  : | Redo: neutron:ports("ebeb4ee6-14be-4ba2-a723-fd62f220b6b9", "f999de49-753e-40c9-9eed-d01ad76bc6c3", "ad058c04-05be-4f56-a76f-7f3b42f36f79", "None", "ACTIVE", "", "True", "07ecce19-d7a4-4c79-924e-1692713e53a7", "e793326db18847e1908e791daa69a5a3", "None", "compute:None", "fa:16:3e:3c:0d:13", "af179309-65f7-4662-a087-e583d6a8bc21", "149f4271-41ca-4b1a-875b-77909debbeac", "bc333f0f-b665-4e2b-97db-a4dd985cb5c8", "None")
  Clas  : | Fail: neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p)
  Clas  : Fail: error(x0)


Recall that there are 2 rules defining *error*.  The part of the trace
occurring before the line break is from one of the rules; the part of the trace
after the line break is from the other.  (The line break does not appear in
the trace--we inserted it for the sake of pedagogy.)

Both rules join the tables neutron:ports, nova:servers, and neutron:networks.  The
trace shows the join being computed one row at a time.  In this case,
we see that there is some port (from neutron:ports) connected to a VM
(from nova:servers) for which there is no record of the port's network
(from neutron:networks).  In this case, there is a row missing from
neutron:networks: the one with ID 07ecce19-d7a4-4c79-924e-1692713e53a7.

At this point, it seems clear that the problem is with the Neutron datasource,
not the rules.



Datasource troubleshooting
--------------------------

At this point, you believe the problem is with one of the datasources.  The first
thing to consider is whether Congress can properly connect to the associated cloud service.
The best way to do that is to examine the tables that the problematic datasource
is exporting.  If the tables being exported by a service is empty, the datasource
driver is not properly connecting to the datasource.

**Check**: Ensure each (relevant) datasource is exporting the tables
the documentation says should be exported::

   $ curl -X GET localhost:1789/v1/data-sources/<ds-id>/tables

To fix connection problems, do both of the following.

    * Ensure the datasource component is enabled in devstack (if you're using devstack)
    * Fix the configuration of the datasource by asking to see its current configuration,
      and if it is wrong, delete that datasource and create a new one with the proper
      configuration.  Don't forget that datasources sometimes return different
      information for different username/password combinations.

Below are examples of how to list datasource configuration, delete an existing datasource,
and create a new datasource::

  # show list and configuration options for each
  $ curl -X GET localhost:1789/v1/data-sources

  # delete old datasource
  $ curl -X DELETE http://127.0.0.1:1789/v1/data-sources/<ds-id>

  # create new datasource
  $ curl -X POST localhost:1789/v1/data-sources -d
   '{"config": {"username": "admin",
                "tenant_name": "admin",
                "password": "password",
                "auth_url": "http://127.0.0.1:5000/v2"},
     "driver": "neutronv2",
     "name": "neutronv2"}'


For example, below we see that the *neutron* datasource is exporting all
the right tables::

    $ curl -X GET localhost:1789/v1/data-sources/<neutron-id>/tables
    {
      "results": [
        {
          "id": "ports.binding_capabilities"
        },
        {
          "id": "routers"
        },
        {
          "id": "ports.extra_dhcp_opts"
        },
        {
          "id": "ports.fixed_ips"
        },
        {
          "id": "ports"
        },
        {
          "id": "ports.fixed_ips_groups"
        },
        {
          "id": "ports.security_groups"
        },
        {
          "id": "networks.subnets"
        },
        {
          "id": "networks"
        },
        {
          "id": "security_groups"
        },
        {
          "id": "ports.address_pairs"
        }
      ]
    }


Once the datasource is properly configured and is returning the proper
list of tables, the next potential problem is that the rows of
one of the tables are incorrect.

**Check**: Ensure the rows of each of the tables exported by the
datasource are correct::

   $ curl -X GET localhost:1789/v1/data-sources/<ds-id>/tables/<table-name>/rows

To check that the rows are correct, you'll need to look at the datasource's schema
to see what each column means and compare that to the
current contents of the actual datasource.

For example, we can look at the rows of the *networks* table in the *neutron*
service.  In this example, there are two rows.  Each row is the value of
the *data* key::

  $ curl -X GET localhost:1789/v1/data-sources/<neutron-id>/tables/networks/rows
  {
    "results": [
      {
        "data": [
          "ACTIVE",
          "public",
          "faf2c578-2893-11e4-b1e3-fa163ebf1676",
          "None",
          "True",
          "d0a7ff9e5d5b4130a586a7af1c855c3e",
          "None",
          "True",
          "False",
          "0d31bf61-c749-4791-8cf2-345f624bad8d",
          "None"
        ]
      },
      {
        "data": [
          "ACTIVE",
          "private",
          "faf31ec4-2893-11e4-b1e3-fa163ebf1676",
          "None",
          "True",
          "e793326db18847e1908e791daa69a5a3",
          "None",
          "False",
          "False",
          "37eee894-a65f-414d-bd8c-a9363293000a",
          "None"
        ]
      }
    ]
  }

Compare these rows to the schema for this datasource::

  $ curl -X GET localhost:1789/v1/data-sources/<neutron-id>/schema

  {'tables': [
    ...
    {'columns': [
      {'description': 'None', 'name': 'status'},
      {'description': 'None', 'name': 'name'},
      {'description': 'None', 'name': 'subnet_group_id'},
      {'description': 'None', 'name': 'provider_physical_network'},
      {'description': 'None', 'name': 'admin_state_up'},
      {'description': 'None', 'name': 'tenant_id'},
      {'description': 'None', 'name': 'provider_network_type'},
      {'description': 'None', 'name': 'router_external'},
      {'description': 'None', 'name': 'shared'},
      {'description': 'None', 'name': 'id'},
      {'description': 'None', 'name': 'provider_segmentation_id'}],
     'table_id': 'networks'},
    ...]}

The schema says the 1st column is the network's status, which in both the
rows above, has the value "ACTIVE".
The schema says the 10th column is the network's ID, which in the
two rows above are 0d31bf61-c749-4791-8cf2-345f624bad8d and
37eee894-a65f-414d-bd8c-a9363293000a.  Notice that the missing network
from our earlier analysis of the policy trace is missing from here as well:
07ecce19-d7a4-4c79-924e-1692713e53a7.

This points to a problem in the configuration of the datasource, in particular
using a username/password combination that does not return all the networks.


Message bus troubleshooting
---------------------------

One thing that sometimes happens is that the datasource has the right rows,
but the policy engine does not.  For example, the *networks* table of the
*neutron* service is not identical to the *neutron:networks* table.
Typically, this means that the policy engine simply hasn't received and
processed the update from the datasource on the message bus.  Waiting
several seconds should fix the problem.


**Check**: Compare the policy engine's version of a table to the datasource's
version.  Remember that the policy engine's name for table T in datasource
D is D:T, e.g. the *networks* table for service *neutron* is named *neutron:networks*::

  curl -X GET localhost:1789/v1/policies/classification/tables/<ds-name>:<table-name>/rows
  curl -X GET localhost:1789/v1/data-sources/<ds-id>/tables/<table-name>/rows


**Warning**: In the current datasource drivers for Neutron and Nova, a
single API call can generate several different tables.  Each table is sent independently
on the message bus, which can lead to inconsistencies between tables (e.g.
table *neutron:ports* might be out of sync with *neutron:ports.security_groups*).
This kind of data skew is an artifact of our implementation and will be
addressed in a future release.  The best solution currently is to wait
until all the messages from the latest polling reach the policy engine.

A similar problem can arise when two datasources are out of sync with each other.
This happens because the two datasources are polled independently.  If something
changes one of the datasources in between when those datasources are polled,
the local cache Congress has will be out of sync.  In a future release, we
will provide machinery for mitigating the impact of these kinds of synchronization
problems.


Production troubleshooting
--------------------------

Another class of problems arises most often in production deployments.
Here we give a couple of problems encountered in production deployments
along with tips for solving them.

1. Log file too big

**Symptom**: slower than normal performance, log size not changing

**Solution**: set up logrotate (a Linux service).  In the directory
  `/etc/logrotate.d`, include a file `congress` and add an entry
  such as the one shown below.  (Here we're assuming the congress log
  is in /var/log/congress)::

    /var/log/congress
    {
      rotate 7
      daily
      missingok
      notifempty
      delaycompress
      compress
      endscript
    }



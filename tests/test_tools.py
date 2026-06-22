from datetime import date

import pytest
from fastmcp import FastMCP

from churchsuite_mcp.tools import register_tools


class StubClient:
    def __init__(self):
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        return {"data": []}


@pytest.mark.asyncio
async def test_list_bookings_drops_none_params_and_maps_array_filters():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("list_bookings")
    await tool.run({"status": "confirmed", "customer_ids": [1, 2]})

    path, params = client.calls[0]
    assert path == "/bookings/bookings"
    assert params == {"status": "confirmed", "customer_ids[]": [1, 2]}


@pytest.mark.asyncio
async def test_get_booking_builds_path_with_id():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("get_booking")
    await tool.run({"id": 42})

    assert client.calls[0] == ("/bookings/bookings/42", None)


@pytest.mark.asyncio
async def test_list_booked_resources_maps_array_filter():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("list_booked_resources")
    await tool.run({"booking_ids": [1, 2]})

    assert client.calls[0] == ("/bookings/booked_resources", {"booking_ids[]": [1, 2]})


@pytest.mark.asyncio
async def test_get_resource_builds_path_with_id():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("get_resource")
    await tool.run({"id": 7})

    assert client.calls[0] == ("/bookings/resources/7", None)


@pytest.mark.asyncio
async def test_list_contacts_drops_none_params_and_maps_array_filters():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("list_contacts")
    await tool.run({"q": "mike", "tag_ids": [1, 2]})

    assert client.calls[0] == (
        "/addressbook/contacts",
        {"q": "mike", "tag_ids[]": [1, 2]},
    )


@pytest.mark.asyncio
async def test_get_contact():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("get_contact")
    await tool.run({"id": 7})

    assert client.calls[0] == ("/addressbook/contacts/7", None)


@pytest.mark.asyncio
async def test_list_ministries_drops_none_params():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("list_ministries")
    await tool.run({"q": "Worship"})

    assert client.calls[0] == ("/rotas/ministries", {"q": "Worship"})


@pytest.mark.asyncio
async def test_list_ministry_members_maps_array_filters():
    client = StubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("list_ministry_members")
    await tool.run({"ministry_ids": [1], "role_ids": [2, 3]})

    assert client.calls[0] == (
        "/rotas/ministry_members",
        {"ministry_ids[]": [1], "role_ids[]": [2, 3]},
    )


class FindServingPatternStubClient:
    def __init__(self):
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        if path == "/rotas/ministry_members":
            return {
                "data": [
                    {
                        "id": 5,
                        "ministry_id": 10,
                        "team_id": 20,
                        "person": {"type": "addressbook_contact", "id": 99},
                        "role_ids": [1, 2],
                    },
                    {
                        "id": 6,
                        "ministry_id": 11,
                        "team_id": 21,
                        "person": {"type": "addressbook_contact", "id": 100},
                        "role_ids": [3],
                    },
                ]
            }
        if path == "/rotas/ministries":
            return {
                "data": [
                    {
                        "id": 10,
                        "name": "Worship",
                        "days": ["sunday"],
                        "starts_at": "09:30",
                        "ends_at": "10:30",
                        "rotation_type": "fortnightly",
                    }
                ]
            }
        raise AssertionError(f"unexpected path: {path}")


@pytest.mark.asyncio
async def test_find_serving_pattern_filters_by_person_and_joins_ministry():
    client = FindServingPatternStubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("find_serving_pattern")
    result = await tool.run({"person_id": 99, "person_type": "addressbook_contact"})

    payload = result.structured_content
    assert len(payload["memberships"]) == 1
    membership = payload["memberships"][0]
    assert membership["ministry_member_id"] == 5
    assert membership["ministry"]["name"] == "Worship"
    assert membership["role_ids"] == [1, 2]


TODAY = date.today().isoformat()


class FindNextBookingForResourceStubClient:
    def __init__(self):
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        if path == "/bookings/resources":
            return {"data": [{"id": 7, "name": "Main Hall"}]}
        if path == "/bookings/booked_resources":
            if params.get("page", 1) == 1:
                return {
                    "data": [
                        {
                            "id": 1,
                            "booking_id": 100,
                            "resource_id": 7,
                            "starts_at": f"{TODAY}T09:00:00Z",
                        },
                        {
                            "id": 2,
                            "booking_id": 101,
                            "resource_id": 7,
                            "starts_at": "2000-01-01T09:00:00Z",
                        },
                        {
                            "id": 3,
                            "booking_id": 102,
                            "resource_id": 8,
                            "starts_at": f"{TODAY}T08:00:00Z",
                        },
                    ],
                    "pagination": {"next_page": 2},
                }
            return {
                "data": [
                    {
                        "id": 4,
                        "booking_id": 103,
                        "resource_id": 7,
                        "starts_at": "2099-01-01T09:00:00Z",
                    },
                ],
                "pagination": {"next_page": None},
            }
        if path == "/bookings/bookings/100":
            return {
                "data": {"id": 100, "name": "Sunday Service", "starts_at": f"{TODAY}T09:00:00Z"}
            }
        raise AssertionError(f"unexpected path: {path}")


@pytest.mark.asyncio
async def test_find_next_booking_for_resource_resolves_name_and_picks_earliest():
    client = FindNextBookingForResourceStubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("find_next_booking_for_resource")
    result = await tool.run({"resource_name": "Main Hall"})

    payload = result.structured_content
    assert payload["resource"]["id"] == 7
    assert payload["booked_resource"]["id"] == 1
    assert payload["booking"]["id"] == 100


@pytest.mark.asyncio
async def test_find_next_booking_for_resource_reports_ambiguous_name():
    class AmbiguousStubClient:
        async def get(self, path, params=None):
            return {"data": [{"id": 1, "name": "Hall A"}, {"id": 2, "name": "Hall B"}]}

    mcp = FastMCP("test")
    register_tools(mcp, AmbiguousStubClient())

    tool = await mcp.get_tool("find_next_booking_for_resource")
    result = await tool.run({"resource_name": "Hall"})

    payload = result.structured_content
    assert payload["next_booking"] is None
    assert len(payload["candidates"]) == 2


class FindNextBookingByNameStubClient:
    def __init__(self):
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        return {
            "data": [
                {"id": 1, "name": "Gibson's Wedding", "starts_at": "2099-06-01T10:00:00Z"},
                {
                    "id": 2,
                    "name": "Gibson's Wedding Rehearsal",
                    "starts_at": "2099-05-01T10:00:00Z",
                },
            ]
        }


@pytest.mark.asyncio
async def test_find_next_booking_by_name_picks_earliest_match():
    client = FindNextBookingByNameStubClient()
    mcp = FastMCP("test")
    register_tools(mcp, client)

    tool = await mcp.get_tool("find_next_booking_by_name")
    result = await tool.run({"name": "Gibson"})

    path, params = client.calls[0]
    assert path == "/bookings/bookings"
    assert params["q"] == "Gibson"
    assert params["status"] == "confirmed"

    payload = result.structured_content
    assert payload["next_booking"]["id"] == 2

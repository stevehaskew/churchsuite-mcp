"""MCP tool definitions for retrieving ChurchSuite bookings."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from fastmcp import FastMCP

from .client import ChurchSuiteClient

BookingStatus = Literal["confirmed", "cancelled", "pending", "declined"]


def _clean_params(params: dict) -> dict:
    """Drop None values so they aren't sent as empty query params."""
    return {key: value for key, value in params.items() if value is not None}


def _today_iso() -> str:
    return date.today().isoformat()


def _day_before(iso_date: str) -> str:
    return (date.fromisoformat(iso_date) - timedelta(days=1)).isoformat()


async def _fetch_all_pages(
    client: ChurchSuiteClient, path: str, params: dict, max_pages: int = 50
) -> list[dict]:
    """Fetch every page of a paginated ChurchSuite list endpoint.

    Used where the API offers no server-side filter (e.g. booked_resources
    has no resource_id or date filter), so we have to pull everything and
    filter client-side.
    """
    results: list[dict] = []
    page = 1
    while True:
        response = await client.get(path, params={**params, "page": page, "per_page": 100})
        results.extend(response.get("data", []))
        next_page = response.get("pagination", {}).get("next_page")
        if not next_page or page >= max_pages:
            break
        page = next_page
    return results


def register_tools(mcp: FastMCP, client: ChurchSuiteClient) -> None:
    @mcp.tool
    async def list_bookings(
        status: BookingStatus | None = None,
        starts_after: str | None = None,
        starts_before: str | None = None,
        customer_ids: list[int] | None = None,
        type_ids: list[int] | None = None,
        q: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List ChurchSuite bookings, optionally filtered by status, date range, customer, type, or a fuzzy search string.

        Dates (starts_after/starts_before) must be in YYYY-MM-DD format.
        """
        params = _clean_params(
            {
                "status": status,
                "starts_after": starts_after,
                "starts_before": starts_before,
                "customer_ids[]": customer_ids,
                "type_ids[]": type_ids,
                "q": q,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/bookings/bookings", params=params)

    @mcp.tool
    async def get_booking(id: int) -> dict:
        """Retrieve a single ChurchSuite booking by its ID."""
        return await client.get(f"/bookings/bookings/{id}")

    @mcp.tool
    async def list_booked_resources(
        booking_ids: list[int] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List resources booked against ChurchSuite bookings, optionally filtered by booking ID."""
        params = _clean_params(
            {
                "booking_ids[]": booking_ids,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/bookings/booked_resources", params=params)

    @mcp.tool
    async def list_resources(
        category: str | None = None,
        q: str | None = None,
        status: Literal["active", "archived"] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List the bookable resources (rooms, equipment, etc.) that can be booked against a booking."""
        params = _clean_params(
            {
                "category": category,
                "q": q,
                "status": status,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/bookings/resources", params=params)

    @mcp.tool
    async def get_resource(id: int) -> dict:
        """Retrieve a single bookable resource by its ID."""
        return await client.get(f"/bookings/resources/{id}")

    @mcp.tool
    async def list_contacts(
        status: Literal["active", "archived", "pending"] | None = None,
        q: str | None = None,
        tag_ids: list[int] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List addressbook contacts, optionally filtered by status, tag, or a fuzzy search string.

        Use this to find a contact's numeric ID (person_id, with person_type
        "addressbook_contact") for use with find_serving_pattern. The fuzzy
        search (q) matches against first_name, last_name, formal_name, email,
        telephone, mobile, address, job, and employer.
        """
        params = _clean_params(
            {
                "status": status,
                "q": q,
                "tag_ids[]": tag_ids,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/addressbook/contacts", params=params)

    @mcp.tool
    async def get_contact(id: int) -> dict:
        """Retrieve a single addressbook contact by its ID."""
        return await client.get(f"/addressbook/contacts/{id}")

    @mcp.tool
    async def list_ministries(
        statuses: list[Literal["active", "archived"]] | None = None,
        q: str | None = None,
        ids: list[int] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List ChurchSuite Rotas ministries (e.g. Worship, Production), optionally filtered by status or name."""
        params = _clean_params(
            {
                "statuses[]": statuses,
                "q": q,
                "ids[]": ids,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/rotas/ministries", params=params)

    @mcp.tool
    async def get_ministry(id: int) -> dict:
        """Retrieve a single Rotas ministry by its ID, including its serving days, times, and rotation type."""
        return await client.get(f"/rotas/ministries/{id}")

    @mcp.tool
    async def list_ministry_teams(
        ministry_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List the teams within Rotas ministries, optionally filtered by ministry or team ID."""
        params = _clean_params(
            {
                "ministry_ids[]": ministry_ids,
                "team_ids[]": team_ids,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/rotas/ministry_teams", params=params)

    @mcp.tool
    async def get_ministry_team(id: int) -> dict:
        """Retrieve a single Rotas ministry team by its ID."""
        return await client.get(f"/rotas/ministry_teams/{id}")

    @mcp.tool
    async def list_ministry_members(
        ministry_ids: list[int] | None = None,
        role_ids: list[int] | None = None,
        team_ids: list[int] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List members of Rotas ministries, optionally filtered by ministry, role, or team.

        Each member links to a person (an addressbook contact or child) via
        person.id and person.type. There is no API filter by person, so to
        find a specific person's memberships, list members for the relevant
        ministries/teams and filter the results by person.id client-side.
        """
        params = _clean_params(
            {
                "ministry_ids[]": ministry_ids,
                "role_ids[]": role_ids,
                "team_ids[]": team_ids,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/rotas/ministry_members", params=params)

    @mcp.tool
    async def list_rota_roles(
        member_ids: list[int] | None = None,
        ministry_ids: list[int] | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict:
        """List the roles (e.g. Worship Leader, Sound Engineer) defined within Rotas ministries."""
        params = _clean_params(
            {
                "member_ids[]": member_ids,
                "ministry_ids[]": ministry_ids,
                "page": page,
                "per_page": per_page,
            }
        )
        return await client.get("/rotas/roles", params=params)

    @mcp.tool
    async def find_serving_pattern(
        person_id: int, person_type: Literal["addressbook_contact", "children_child"]
    ) -> dict:
        """Find which Rotas ministries/teams/roles a person belongs to, and their typical serving pattern.

        IMPORTANT: ChurchSuite's API v2 does not expose individual rota slot
        assignments or dates, only ministry membership and a ministry's
        recurring schedule definition (days, starts_at/ends_at, rotation_type).
        This tool cannot tell you the exact next date someone is rostered on;
        it returns the ministries they serve in plus that ministry's
        recurrence pattern so you can describe roughly how often/when they
        serve (e.g. "fortnightly on Sundays at 09:30"). For a confirmed next
        serving date, the user should check My ChurchSuite directly.
        """
        members_response = await client.get("/rotas/ministry_members", params={"per_page": 100})
        matches = [
            member
            for member in members_response.get("data", [])
            if member.get("person", {}).get("id") == person_id
            and member.get("person", {}).get("type") == person_type
        ]

        ministry_ids = sorted({member["ministry_id"] for member in matches})
        ministries_by_id = {}
        if ministry_ids:
            ministries_response = await client.get(
                "/rotas/ministries", params={"ids[]": ministry_ids, "per_page": 100}
            )
            ministries_by_id = {m["id"]: m for m in ministries_response.get("data", [])}

        results = []
        for member in matches:
            ministry = ministries_by_id.get(member["ministry_id"])
            results.append(
                {
                    "ministry_member_id": member["id"],
                    "ministry": ministry,
                    "team_id": member.get("team_id"),
                    "role_ids": member.get("role_ids", []),
                }
            )

        return {
            "person": {"id": person_id, "type": person_type},
            "memberships": results,
            "note": (
                "ChurchSuite's API does not expose actual rota slot dates, only "
                "ministry membership and recurrence pattern (days/time/rotation_type)."
            ),
        }

    @mcp.tool
    async def find_next_booking_for_resource(
        resource_id: int | None = None,
        resource_name: str | None = None,
        from_date: str | None = None,
    ) -> dict:
        """Find the next upcoming booking that has a specific resource booked against it.

        Provide either resource_id, or resource_name to resolve it via a fuzzy
        search against /bookings/resources (must match exactly one resource).
        from_date (YYYY-MM-DD) is inclusive and defaults to today.

        Note: ChurchSuite's API has no resource or date filter on
        /bookings/booked_resources, so this fetches every booked resource
        record and filters client-side - it may be slow on accounts with a
        long booking history.
        """
        if resource_id is None:
            if not resource_name:
                raise ValueError("Provide either resource_id or resource_name.")
            resources_response = await client.get(
                "/bookings/resources", params={"q": resource_name, "per_page": 50}
            )
            candidates = resources_response.get("data", [])
            if not candidates:
                return {
                    "next_booking": None,
                    "note": f"No resource found matching '{resource_name}'.",
                }
            if len(candidates) > 1:
                return {
                    "next_booking": None,
                    "note": f"Multiple resources match '{resource_name}'; narrow the search or pass resource_id.",
                    "candidates": [{"id": r["id"], "name": r.get("name")} for r in candidates],
                }
            resource = candidates[0]
            resource_id = resource["id"]
        else:
            resource = (await client.get(f"/bookings/resources/{resource_id}")).get("data")

        threshold = from_date or _today_iso()
        booked_resources = await _fetch_all_pages(client, "/bookings/booked_resources", {})
        upcoming = [
            br
            for br in booked_resources
            if br.get("resource_id") == resource_id and br.get("starts_at", "") >= threshold
        ]
        if not upcoming:
            return {
                "resource": resource,
                "next_booking": None,
                "note": "No upcoming bookings found for this resource.",
            }

        next_booked_resource = min(upcoming, key=lambda br: br["starts_at"])
        booking = (
            await client.get(f"/bookings/bookings/{next_booked_resource['booking_id']}")
        ).get("data")
        return {
            "resource": resource,
            "booked_resource": next_booked_resource,
            "booking": booking,
        }

    @mcp.tool
    async def find_next_booking_by_name(
        name: str,
        from_date: str | None = None,
        status: BookingStatus | None = "confirmed",
    ) -> dict:
        """Find the next upcoming booking whose name/title fuzzy-matches the given string.

        Searches /bookings/bookings by name (ChurchSuite's q filter also
        matches date, reference, and sequence_id). from_date (YYYY-MM-DD) is
        inclusive and defaults to today.
        """
        threshold = from_date or _today_iso()
        params = _clean_params(
            {
                "q": name,
                "starts_after": _day_before(threshold),
                "status": status,
                "per_page": 100,
            }
        )
        response = await client.get("/bookings/bookings", params=params)
        matches = [b for b in response.get("data", []) if b.get("starts_at", "") >= threshold]
        if not matches:
            return {"next_booking": None, "note": f"No upcoming booking found matching '{name}'."}

        return {"next_booking": min(matches, key=lambda b: b["starts_at"])}

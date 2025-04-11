"""
MCP server for Odoo integration

Provides MCP tools and resources for interacting with Odoo ERP systems
"""

import json
import os
import sys
import requests
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from .odoo_client import OdooClient, get_odoo_client


@dataclass
class AppContext:
    """Application context for the MCP server"""

    odoo: OdooClient


@asynccontextmanager
async def app_lifespan(_: FastMCP) -> AsyncIterator[AppContext]:
    """
    Application lifespan for initialization and cleanup
    """
    # Initialize Odoo client on startup
    odoo_client = get_odoo_client()

    try:
        yield AppContext(odoo=odoo_client)
    finally:
        # No cleanup needed for Odoo client
        pass


# Create MCP server
mcp = FastMCP(
    "Odoo MCP Server",
    description="MCP Server for interacting with Odoo ERP systems",
    dependencies=["requests"],
    lifespan=app_lifespan,
)


# ----- MCP Resources -----


@mcp.resource(
    "odoo://models", description="List all available models in the Odoo system"
)
def get_models() -> str:
    """Lists all available models in the Odoo system"""
    odoo_client = get_odoo_client()
    models = odoo_client.get_models()
    return json.dumps(models, indent=2)


@mcp.resource(
    "odoo://model/{model_name}",
    description="Get detailed information about a specific model including fields",
)
def get_model_info(model_name: str) -> str:
    """
    Get information about a specific model

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    odoo_client = get_odoo_client()
    try:
        # Get model info
        model_info = odoo_client.get_model_info(model_name)

        # Get field definitions
        fields = odoo_client.get_model_fields(model_name)
        model_info["fields"] = fields

        return json.dumps(model_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://record/{model_name}/{record_id}",
    description="Get detailed information of a specific record by ID",
)
def get_record(model_name: str, record_id: str) -> str:
    """
    Get a specific record by ID

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        record_id: ID of the record
    """
    odoo_client = get_odoo_client()
    try:
        record_id_int = int(record_id)
        record = odoo_client.read_records(model_name, [record_id_int])
        if not record:
            return json.dumps(
                {"error": f"Record not found: {model_name} ID {record_id}"}, indent=2
            )
        return json.dumps(record[0], indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://search/{model_name}/{domain}",
    description="Search for records matching the domain",
)
def search_records_resource(model_name: str, domain: str) -> str:
    """
    Search for records that match a domain

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        domain: Search domain in JSON format (e.g., '[["name", "ilike", "test"]]')
    """
    odoo_client = get_odoo_client()
    try:
        # Parse domain from JSON string
        domain_list = json.loads(domain)

        # Set a reasonable default limit
        limit = 10

        # Perform search_read for efficiency
        results = odoo_client.search_read(model_name, domain_list, limit=limit)

        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ----- Pydantic models for type safety -----


class DomainCondition(BaseModel):
    """A single condition in a search domain"""

    field: str = Field(description="Field name to search")
    operator: str = Field(
        description="Operator (e.g., '=', '!=', '>', '<', 'in', 'not in', 'like', 'ilike')"
    )
    value: Any = Field(description="Value to compare against")

    def to_tuple(self) -> List:
        """Convert to Odoo domain condition tuple"""
        return [self.field, self.operator, self.value]


class SearchDomain(BaseModel):
    """Search domain for Odoo models"""

    conditions: List[DomainCondition] = Field(
        default_factory=list,
        description="List of conditions for searching. All conditions are combined with AND operator.",
    )

    def to_domain_list(self) -> List[List]:
        """Convert to Odoo domain list format"""
        return [condition.to_tuple() for condition in self.conditions]


class EmployeeSearchResult(BaseModel):
    """Represents a single employee search result."""

    id: int = Field(description="Employee ID")
    name: str = Field(description="Employee name")


class SearchEmployeeResponse(BaseModel):
    """Response model for the search_employee tool."""

    success: bool = Field(description="Indicates if the search was successful")
    result: Optional[List[EmployeeSearchResult]] = Field(
        default=None, description="List of employee search results"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class Holiday(BaseModel):
    """Represents a single holiday."""

    display_name: str = Field(description="Display name of the holiday")
    start_datetime: str = Field(description="Start date and time of the holiday")
    stop_datetime: str = Field(description="End date and time of the holiday")
    employee_id: List[Union[int, str]] = Field(
        description="Employee ID associated with the holiday"
    )
    name: str = Field(description="Name of the holiday")
    state: str = Field(description="State of the holiday")


class SearchHolidaysResponse(BaseModel):
    """Response model for the search_holidays tool."""

    success: bool = Field(description="Indicates if the search was successful")
    result: Optional[List[Holiday]] = Field(
        default=None, description="List of holidays found"
    )
    error: Optional[str] = Field(default=None, description="Error message, if any")


class ProductDescriptionRequest(BaseModel):
    """Request model for the generate_product_description tool."""

    account_id: str = Field(description="Account ID")
    product_id: int = Field(description="Product ID in Odoo")


class ProductDescriptionResponse(BaseModel):
    """Response model for the generate_product_description tool."""

    success: bool = Field(description="Indicates if the description generation was successful")
    description: Optional[str] = Field(default=None, description="Generated description")
    product_id: Optional[int] = Field(default=None, description="Product ID")
    error: Optional[str] = Field(default=None, description="Error message, if any")


class SyncProductRequest(BaseModel):
    """Request model for the sync_product_to_vector_db tool."""

    account_id: str = Field(description="Account ID")
    product_id: int = Field(description="Product ID in Odoo")
    description: Optional[str] = Field(default=None, description="Product description to use for vectorization")
    skip_odoo_update: bool = Field(default=False, description="Skip updating Odoo with sync status")


class SyncProductResponse(BaseModel):
    """Response model for the sync_product_to_vector_db tool."""

    success: bool = Field(description="Indicates if the synchronization was successful")
    vector_id: Optional[str] = Field(default=None, description="Vector ID in Qdrant")
    message: Optional[str] = Field(default=None, description="Success message")
    error: Optional[str] = Field(default=None, description="Error message, if any")


class SemanticSearchRequest(BaseModel):
    """Request model for the semantic_search tool."""

    account_id: str = Field(description="Account ID")
    query: str = Field(description="Search query in natural language")
    limit: int = Field(default=10, description="Maximum number of results to return")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class SemanticSearchResponse(BaseModel):
    """Response model for the semantic_search tool."""

    success: bool = Field(description="Indicates if the search was successful")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Search results")
    count: Optional[int] = Field(default=None, description="Number of results")
    error: Optional[str] = Field(default=None, description="Error message, if any")


# ----- MCP Tools -----


@mcp.tool(description="Execute a custom method on an Odoo model")
def execute_method(
    ctx: Context,
    model: str,
    method: str,
    args: List = None,
    kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a custom method on an Odoo model

    Parameters:
        model: The model name (e.g., 'res.partner')
        method: Method name to execute
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - result: Result of the method (if success)
        - error: Error message (if failure)
    """
    odoo = ctx.request_context.lifespan_context.odoo
    try:
        args = args or []
        kwargs = kwargs or {}

        # Special handling for search methods like search, search_count, search_read
        search_methods = ["search", "search_count", "search_read"]
        if method in search_methods and args:
            # Search methods usually have domain as the first parameter
            # args: [[domain], limit, offset, ...] or [domain, limit, offset, ...]
            normalized_args = list(
                args
            )  # Create a copy to avoid affecting the original args

            if len(normalized_args) > 0:
                # Process domain in args[0]
                domain = normalized_args[0]
                domain_list = []

                # Check if domain is wrapped unnecessarily ([domain] instead of domain)
                if (
                    isinstance(domain, list)
                    and len(domain) == 1
                    and isinstance(domain[0], list)
                ):
                    # Case [[domain]] - unwrap to [domain]
                    domain = domain[0]

                # Normalize domain similar to search_records function
                if domain is None:
                    domain_list = []
                elif isinstance(domain, dict):
                    if "conditions" in domain:
                        # Object format
                        conditions = domain.get("conditions", [])
                        domain_list = []
                        for cond in conditions:
                            if isinstance(cond, dict) and all(
                                k in cond for k in ["field", "operator", "value"]
                            ):
                                domain_list.append(
                                    [cond["field"], cond["operator"], cond["value"]]
                                )
                elif isinstance(domain, list):
                    # List format
                    if not domain:
                        domain_list = []
                    elif all(isinstance(item, list) for item in domain) or any(
                        item in ["&", "|", "!"] for item in domain
                    ):
                        domain_list = domain
                    elif len(domain) >= 3 and isinstance(domain[0], str):
                        # Case [field, operator, value] (not [[field, operator, value]])
                        domain_list = [domain]
                elif isinstance(domain, str):
                    # String format (JSON)
                    try:
                        parsed_domain = json.loads(domain)
                        if (
                            isinstance(parsed_domain, dict)
                            and "conditions" in parsed_domain
                        ):
                            conditions = parsed_domain.get("conditions", [])
                            domain_list = []
                            for cond in conditions:
                                if isinstance(cond, dict) and all(
                                    k in cond for k in ["field", "operator", "value"]
                                ):
                                    domain_list.append(
                                        [cond["field"], cond["operator"], cond["value"]]
                                    )
                        elif isinstance(parsed_domain, list):
                            domain_list = parsed_domain
                    except json.JSONDecodeError:
                        try:
                            import ast

                            parsed_domain = ast.literal_eval(domain)
                            if isinstance(parsed_domain, list):
                                domain_list = parsed_domain
                        except:
                            domain_list = []

                # Xác thực domain_list
                if domain_list:
                    valid_conditions = []
                    for cond in domain_list:
                        if isinstance(cond, str) and cond in ["&", "|", "!"]:
                            valid_conditions.append(cond)
                            continue

                        if (
                            isinstance(cond, list)
                            and len(cond) == 3
                            and isinstance(cond[0], str)
                            and isinstance(cond[1], str)
                        ):
                            valid_conditions.append(cond)

                    domain_list = valid_conditions

                # Cập nhật args với domain đã chuẩn hóa
                normalized_args[0] = domain_list
                args = normalized_args

                # Log for debugging
                print(f"Executing {method} with normalized domain: {domain_list}")

        result = odoo.execute_method(model, method, *args, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool(description="Search for employees by name")
def search_employee(
    ctx: Context,
    name: str,
    limit: int = 20,
) -> SearchEmployeeResponse:
    """
    Search for employees by name using Odoo's name_search method.

    Parameters:
        name: The name (or part of the name) to search for.
        limit: The maximum number of results to return (default 20).

    Returns:
        SearchEmployeeResponse containing results or error information.
    """
    odoo = ctx.request_context.lifespan_context.odoo
    model = "hr.employee"
    method = "name_search"

    args = []
    kwargs = {"name": name, "limit": limit}

    try:
        result = odoo.execute_method(model, method, *args, **kwargs)
        parsed_result = [
            EmployeeSearchResult(id=item[0], name=item[1]) for item in result
        ]
        return SearchEmployeeResponse(success=True, result=parsed_result)
    except Exception as e:
        return SearchEmployeeResponse(success=False, error=str(e))


@mcp.tool(description="Search for holidays within a date range")
def search_holidays(
    ctx: Context,
    start_date: str,
    end_date: str,
    employee_id: Optional[int] = None,
) -> SearchHolidaysResponse:
    """
    Searches for holidays within a specified date range.

    Parameters:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        employee_id: Optional employee ID to filter holidays.

    Returns:
        SearchHolidaysResponse:  Object containing the search results.
    """
    odoo = ctx.request_context.lifespan_context.odoo

    # Validate date format using datetime
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return SearchHolidaysResponse(
            success=False, error="Invalid start_date format. Use YYYY-MM-DD."
        )
    try:
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return SearchHolidaysResponse(
            success=False, error="Invalid end_date format. Use YYYY-MM-DD."
        )

    # Calculate adjusted start_date (subtract one day)
    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    adjusted_start_date_dt = start_date_dt - timedelta(days=1)
    adjusted_start_date = adjusted_start_date_dt.strftime("%Y-%m-%d")

    # Build the domain
    domain = [
        "&",
        ["start_datetime", "<=", f"{end_date} 22:59:59"],
        # Use adjusted date
        ["stop_datetime", ">=", f"{adjusted_start_date} 23:00:00"],
    ]
    if employee_id:
        domain.append(
            ["employee_id", "=", employee_id],
        )

    try:
        holidays = odoo.search_read(
            model_name="hr.leave.report.calendar",
            domain=domain,
        )
        parsed_holidays = [Holiday(**holiday) for holiday in holidays]
        return SearchHolidaysResponse(success=True, result=parsed_holidays)

    except Exception as e:
        return SearchHolidaysResponse(success=False, error=str(e))


# ----- Sales Order Tools -----

class SaleOrderLine(BaseModel):
    """Represents a single sale order line"""

    product_id: int = Field(description="Product ID")
    product_uom_qty: float = Field(description="Quantity")
    price_unit: Optional[float] = Field(None, description="Unit price (optional)")
    discount: Optional[float] = Field(None, description="Discount percentage (optional)")
    name: Optional[str] = Field(None, description="Description (optional)")


class SaleOrderResponse(BaseModel):
    """Response model for sale order operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    order_id: Optional[int] = Field(None, description="Sale order ID if created/updated")
    result: Optional[Any] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Create a sales order")
def create_sales_order(
    ctx: Context,
    partner_id: int,
    order_lines: List[Dict[str, Any]],
    date_order: Optional[str] = None,
    payment_term_id: Optional[int] = None,
    pricelist_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    team_id: Optional[int] = None,
    client_order_ref: Optional[str] = None,
) -> SaleOrderResponse:
    """
    Create a new sales order (quotation)

    Parameters:
        partner_id: Customer ID
        order_lines: List of order lines with product_id and product_uom_qty
        date_order: Order date (optional, default is current date)
        payment_term_id: Payment term ID (optional)
        pricelist_id: Pricelist ID (optional)
        warehouse_id: Warehouse ID (optional)
        team_id: Sales team ID (optional)
        client_order_ref: Customer reference (optional)

    Returns:
        SaleOrderResponse containing the result
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Prepare order lines in Odoo format (0, 0, values)
        formatted_lines = []
        for line in order_lines:
            line_values = {
                'product_id': line['product_id'],
                'product_uom_qty': line['product_uom_qty']
            }

            # Add optional fields if provided
            if 'price_unit' in line and line['price_unit'] is not None:
                line_values['price_unit'] = line['price_unit']
            if 'discount' in line and line['discount'] is not None:
                line_values['discount'] = line['discount']
            if 'name' in line and line['name'] is not None:
                line_values['name'] = line['name']

            formatted_lines.append((0, 0, line_values))

        # Prepare order values
        order_values = {
            'partner_id': partner_id,
            'order_line': formatted_lines,
        }

        # Add optional fields if provided
        if date_order:
            order_values['date_order'] = date_order
        if payment_term_id:
            order_values['payment_term_id'] = payment_term_id
        if pricelist_id:
            order_values['pricelist_id'] = pricelist_id
        if warehouse_id:
            order_values['warehouse_id'] = warehouse_id
        if team_id:
            order_values['team_id'] = team_id
        if client_order_ref:
            order_values['client_order_ref'] = client_order_ref

        # Create the sales order
        order_id = odoo.execute_method('sale.order', 'create', order_values)

        return SaleOrderResponse(
            success=True,
            order_id=order_id,
            result={'order_id': order_id}
        )
    except Exception as e:
        return SaleOrderResponse(success=False, error=str(e))


@mcp.tool(description="Confirm a sales order")
def confirm_sales_order(
    ctx: Context,
    order_id: int,
) -> SaleOrderResponse:
    """
    Confirm a sales order (convert quotation to order)

    Parameters:
        order_id: Sales order ID to confirm

    Returns:
        SaleOrderResponse containing the result
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Call the action_confirm method on the sales order
        result = odoo.execute_method('sale.order', 'action_confirm', [order_id])

        return SaleOrderResponse(
            success=True,
            order_id=order_id,
            result=result
        )
    except Exception as e:
        return SaleOrderResponse(success=False, error=str(e))


@mcp.tool(description="Create invoice from sales order")
def create_invoice_from_sales_order(
    ctx: Context,
    order_id: int,
    advance_payment_method: str = 'delivered',
) -> SaleOrderResponse:
    """
    Create invoice from a sales order

    Parameters:
        order_id: Sales order ID
        advance_payment_method: Method for advance payment ('delivered', 'all', 'percentage', 'fixed')

    Returns:
        SaleOrderResponse containing the result
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Create a sale.advance.payment.inv record
        payment_values = {
            'advance_payment_method': advance_payment_method,
        }

        # If percentage or fixed amount is selected, additional fields are required
        if advance_payment_method == 'percentage':
            payment_values['amount'] = 100  # 100% by default
        elif advance_payment_method == 'fixed':
            payment_values['fixed_amount'] = 0.0  # Must be set by caller

        payment_id = odoo.execute_method('sale.advance.payment.inv', 'create', payment_values)

        # Call create_invoices with the active_ids context
        context = {'active_ids': [order_id]}
        result = odoo.execute_method(
            'sale.advance.payment.inv',
            'create_invoices',
            [payment_id],
            {'context': context}
        )

        # Get the created invoice ID(s)
        invoice_ids = []
        if result and isinstance(result, dict) and 'domain' in result:
            # Extract invoice IDs from the domain
            for condition in result['domain']:
                if condition[0] == 'id' and condition[1] == 'in':
                    invoice_ids = condition[2]
                    break

        return SaleOrderResponse(
            success=True,
            order_id=order_id,
            result={'invoice_ids': invoice_ids}
        )
    except Exception as e:
        return SaleOrderResponse(success=False, error=str(e))


# ----- Calendar Event Tools -----

class CalendarEvent(BaseModel):
    """Represents a calendar event"""

    id: Optional[int] = Field(None, description="Event ID")
    name: str = Field(description="Event name/title")
    start: str = Field(description="Start date and time (YYYY-MM-DD HH:MM:SS)")
    stop: str = Field(description="End date and time (YYYY-MM-DD HH:MM:SS)")
    allday: Optional[bool] = Field(False, description="All day event flag")
    partner_ids: List[int] = Field(description="List of partner IDs to invite")
    location: Optional[str] = Field(None, description="Event location")
    description: Optional[str] = Field(None, description="Event description")


class CalendarEventResponse(BaseModel):
    """Response model for calendar event operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    event_id: Optional[int] = Field(None, description="Calendar event ID if created/updated")
    result: Optional[Any] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Create a calendar event/appointment")
def create_calendar_event(
    ctx: Context,
    name: str,
    start: str,
    stop: str,
    partner_ids: List[int],
    allday: bool = False,
    location: Optional[str] = None,
    description: Optional[str] = None,
) -> CalendarEventResponse:
    """
    Create a new calendar event or appointment

    Parameters:
        name: Event name/title
        start: Start date and time (YYYY-MM-DD HH:MM:SS)
        stop: End date and time (YYYY-MM-DD HH:MM:SS)
        partner_ids: List of partner IDs to invite
        allday: All day event flag (default: False)
        location: Event location (optional)
        description: Event description (optional)

    Returns:
        CalendarEventResponse containing the result
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Validate date formats
        try:
            datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            datetime.strptime(stop, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return CalendarEventResponse(
                success=False,
                error="Invalid date format. Use YYYY-MM-DD HH:MM:SS format."
            )

        # Prepare event values
        event_values = {
            'name': name,
            'start': start,
            'stop': stop,
            'allday': allday,
            'partner_ids': [(6, 0, partner_ids)],  # (6, 0, ids) means replace with these ids
        }

        # Add optional fields if provided
        if location:
            event_values['location'] = location
        if description:
            event_values['description'] = description

        # Create the calendar event
        event_id = odoo.execute_method('calendar.event', 'create', event_values)

        return CalendarEventResponse(
            success=True,
            event_id=event_id,
            result={'event_id': event_id}
        )
    except Exception as e:
        return CalendarEventResponse(success=False, error=str(e))


@mcp.tool(description="Check calendar availability for a time slot")
def check_calendar_availability(
    ctx: Context,
    start: str,
    stop: str,
    partner_ids: List[int],
) -> CalendarEventResponse:
    """
    Check if a time slot is available for all specified partners

    Parameters:
        start: Start date and time (YYYY-MM-DD HH:MM:SS)
        stop: End date and time (YYYY-MM-DD HH:MM:SS)
        partner_ids: List of partner IDs to check availability for

    Returns:
        CalendarEventResponse containing the result
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Validate date formats
        try:
            datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            datetime.strptime(stop, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return CalendarEventResponse(
                success=False,
                error="Invalid date format. Use YYYY-MM-DD HH:MM:SS format."
            )

        # Check for conflicting events for each partner
        conflicts = []
        for partner_id in partner_ids:
            # Build domain to search for conflicting events
            domain = [
                '&',
                '&',
                ('partner_ids', 'in', [partner_id]),
                ('stop', '>', start),
                ('start', '<', stop),
            ]

            # Search for conflicting events
            conflicting_events = odoo.search_read(
                model_name="calendar.event",
                domain=domain,
                fields=['id', 'name', 'start', 'stop', 'partner_ids'],
            )

            if conflicting_events:
                partner_name = odoo.read_records('res.partner', [partner_id], ['name'])[0]['name']
                conflicts.append({
                    'partner_id': partner_id,
                    'partner_name': partner_name,
                    'conflicting_events': conflicting_events
                })

        # Return availability result
        is_available = len(conflicts) == 0
        return CalendarEventResponse(
            success=True,
            result={
                'is_available': is_available,
                'conflicts': conflicts if not is_available else []
            }
        )
    except Exception as e:
        return CalendarEventResponse(success=False, error=str(e))


# ----- Product Tools -----

class ProductSearchResponse(BaseModel):
    """Response model for product search operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    products: Optional[List[Dict[str, Any]]] = Field(None, description="List of products found")
    count: Optional[int] = Field(None, description="Total count of matching products")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Search for products with various criteria")
def search_products(
    ctx: Context,
    query: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    order: Optional[str] = None,
    include_variants: bool = True,
    active_only: bool = True,
    fields: Optional[List[str]] = None,
) -> ProductSearchResponse:
    """
    Search for products based on various criteria

    Parameters:
        query: Text to search in product name and description (optional)
        category_id: Product category ID to filter by (optional)
        limit: Maximum number of records to return (default: 10)
        offset: Number of records to skip (default: 0)
        order: Sorting order (e.g., 'name ASC, id DESC') (optional)
        include_variants: Whether to include product variants (default: True)
        active_only: Whether to include only active products (default: True)
        fields: List of fields to return (optional, returns standard fields if not specified)

    Returns:
        ProductSearchResponse containing the search results
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Determine which model to use based on include_variants flag
        model = 'product.product' if include_variants else 'product.template'

        # Build domain
        domain = []

        # Add active filter if requested
        if active_only:
            domain.append(('active', '=', True))

        # Add text search if provided
        if query:
            domain.append('|')
            domain.append(('name', 'ilike', query))
            domain.append(('description', 'ilike', query))

        # Add category filter if provided
        if category_id:
            domain.append(('categ_id', '=', category_id))

        # Set default fields if not specified
        if not fields:
            fields = ['id', 'name', 'default_code', 'list_price', 'categ_id', 'description', 'image_small']

        # Get total count (without limit)
        count = odoo.execute_method(model, 'search_count', domain)

        # Perform search with limit and offset
        products = odoo.search_read(
            model_name=model,
            domain=domain,
            fields=fields,
            limit=limit,
            offset=offset,
            order=order
        )

        return ProductSearchResponse(
            success=True,
            products=products,
            count=count
        )
    except Exception as e:
        return ProductSearchResponse(success=False, error=str(e))


# ----- Customer Tools -----

class CustomerSearchResponse(BaseModel):
    """Response model for customer search operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    customers: Optional[List[Dict[str, Any]]] = Field(None, description="List of customers found")
    count: Optional[int] = Field(None, description="Total count of matching customers")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Search for customers with various criteria")
def search_customers(
    ctx: Context,
    query: Optional[str] = None,
    customer_type: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    order: Optional[str] = None,
    active_only: bool = True,
    fields: Optional[List[str]] = None,
) -> CustomerSearchResponse:
    """
    Search for customers based on various criteria

    Parameters:
        query: Text to search in customer name, email, or reference (optional)
        customer_type: Type of customer ('company' or 'person') (optional)
        limit: Maximum number of records to return (default: 10)
        offset: Number of records to skip (default: 0)
        order: Sorting order (e.g., 'name ASC, id DESC') (optional)
        active_only: Whether to include only active customers (default: True)
        fields: List of fields to return (optional, returns standard fields if not specified)

    Returns:
        CustomerSearchResponse containing the search results
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Build domain
        domain = [('customer_rank', '>', 0)]  # Only customers

        # Add active filter if requested
        if active_only:
            domain.append(('active', '=', True))

        # Add text search if provided
        if query:
            domain.extend(['|', '|', '|',
                ('name', 'ilike', query),
                ('email', 'ilike', query),
                ('phone', 'ilike', query),
                ('ref', 'ilike', query)
            ])

        # Add customer type filter if provided
        if customer_type:
            if customer_type.lower() == 'company':
                domain.append(('is_company', '=', True))
            elif customer_type.lower() == 'person':
                domain.append(('is_company', '=', False))

        # Set default fields if not specified
        if not fields:
            fields = ['id', 'name', 'email', 'phone', 'mobile', 'street', 'city', 'country_id', 'is_company']

        # Get total count (without limit)
        count = odoo.execute_method('res.partner', 'search_count', domain)

        # Perform search with limit and offset
        customers = odoo.search_read(
            model_name='res.partner',
            domain=domain,
            fields=fields,
            limit=limit,
            offset=offset,
            order=order
        )

        return CustomerSearchResponse(
            success=True,
            customers=customers,
            count=count
        )
    except Exception as e:
        return CustomerSearchResponse(success=False, error=str(e))


# ----- Inventory Tools -----

class StockQuantityResponse(BaseModel):
    """Response model for stock quantity operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    quantities: Optional[Dict[int, float]] = Field(None, description="Dictionary mapping product IDs to quantities")
    detailed_quantities: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed quantity information by location")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Get stock quantities for products")
def get_stock_quantities(
    ctx: Context,
    product_ids: List[int],
    warehouse_id: Optional[int] = None,
    location_id: Optional[int] = None,
    detailed: bool = False,
) -> StockQuantityResponse:
    """
    Get stock quantities for specified products

    Parameters:
        product_ids: List of product IDs to check stock for
        warehouse_id: Specific warehouse ID to check (optional)
        location_id: Specific stock location ID to check (optional)
        detailed: Whether to return detailed information by location (default: False)

    Returns:
        StockQuantityResponse containing the stock quantities
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Build domain for stock quants
        domain = [('product_id', 'in', product_ids)]

        # Add location filter if provided
        if location_id:
            domain.append(('location_id', '=', location_id))
        elif warehouse_id:
            # Get stock locations for the warehouse
            warehouse = odoo.read_records('stock.warehouse', [warehouse_id], ['lot_stock_id'])
            if warehouse and warehouse[0]['lot_stock_id']:
                location_id = warehouse[0]['lot_stock_id'][0]
                domain.append(('location_id', 'child_of', location_id))
        else:
            # Only include internal locations
            internal_locations = odoo.execute_method(
                'stock.location',
                'search',
                [('usage', '=', 'internal')]
            )
            if internal_locations:
                domain.append(('location_id', 'in', internal_locations))

        # Get quantities
        if detailed:
            # Get detailed quantities by location
            quants = odoo.search_read(
                model_name='stock.quant',
                domain=domain,
                fields=['product_id', 'location_id', 'quantity', 'reserved_quantity']
            )

            # Calculate available quantities
            detailed_quantities = []
            for quant in quants:
                quant['available_quantity'] = quant['quantity'] - quant['reserved_quantity']
                detailed_quantities.append(quant)

            # Also calculate total quantities per product
            quantities = {}
            for product_id in product_ids:
                product_quants = [q for q in quants if q['product_id'][0] == product_id]
                total_qty = sum(q['available_quantity'] for q in product_quants)
                quantities[product_id] = total_qty

            return StockQuantityResponse(
                success=True,
                quantities=quantities,
                detailed_quantities=detailed_quantities
            )
        else:
            # Just get total quantities per product
            quantities = {}
            for product_id in product_ids:
                product_domain = domain + [('product_id', '=', product_id)]
                quants = odoo.search_read(
                    model_name='stock.quant',
                    domain=product_domain,
                    fields=['quantity', 'reserved_quantity']
                )
                total_qty = sum(q['quantity'] - q['reserved_quantity'] for q in quants)
                quantities[product_id] = total_qty

            return StockQuantityResponse(
                success=True,
                quantities=quantities
            )
    except Exception as e:
        return StockQuantityResponse(success=False, error=str(e))


# ----- Pricing Tools -----

class ProductPriceResponse(BaseModel):
    """Response model for product price operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    prices: Optional[Dict[int, float]] = Field(None, description="Dictionary mapping product IDs to prices")
    detailed_prices: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed price information")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Get product prices for a specific customer")
def get_product_prices(
    ctx: Context,
    product_ids: List[int],
    partner_id: int,
    pricelist_id: Optional[int] = None,
    quantity: float = 1.0,
    date: Optional[str] = None,
    detailed: bool = False,
) -> ProductPriceResponse:
    """
    Get product prices for a specific customer

    Parameters:
        product_ids: List of product IDs to get prices for
        partner_id: Customer/partner ID
        pricelist_id: Specific pricelist ID to use (optional, uses partner's pricelist if not specified)
        quantity: Quantity for price calculation (default: 1.0)
        date: Date for price calculation in YYYY-MM-DD format (optional, uses current date if not specified)
        detailed: Whether to return detailed price information (default: False)

    Returns:
        ProductPriceResponse containing the prices
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Get partner's pricelist if not specified
        if not pricelist_id:
            partner = odoo.read_records('res.partner', [partner_id], ['property_product_pricelist'])
            if partner and partner[0]['property_product_pricelist']:
                pricelist_id = partner[0]['property_product_pricelist'][0]
            else:
                # Get default pricelist
                default_pricelists = odoo.execute_method(
                    'product.pricelist',
                    'search',
                    [('active', '=', True)],
                    {'limit': 1}
                )
                if default_pricelists:
                    pricelist_id = default_pricelists[0]
                else:
                    return ProductPriceResponse(
                        success=False,
                        error="No pricelist found for the partner and no default pricelist available."
                    )

        # Prepare context for price calculation
        context = {
            'pricelist': pricelist_id,
            'partner': partner_id,
            'quantity': quantity,
        }

        if date:
            context['date'] = date

        # Get prices
        prices = {}
        detailed_prices = []

        for product_id in product_ids:
            # Get product price using get_product_price method
            price = odoo.execute_method(
                'product.pricelist',
                'get_product_price',
                pricelist_id, product_id, quantity, partner_id, date
            )

            prices[product_id] = price

            if detailed:
                # Get detailed price information
                product_info = odoo.read_records('product.product', [product_id], ['name', 'list_price', 'standard_price'])

                if product_info:
                    detailed_prices.append({
                        'product_id': product_id,
                        'name': product_info[0]['name'],
                        'list_price': product_info[0]['list_price'],  # Public price
                        'standard_price': product_info[0]['standard_price'],  # Cost
                        'calculated_price': price,  # Price after applying pricelist rules
                        'discount': round((1 - price / product_info[0]['list_price']) * 100, 2) if product_info[0]['list_price'] else 0,
                    })

        if detailed:
            return ProductPriceResponse(
                success=True,
                prices=prices,
                detailed_prices=detailed_prices
            )
        else:
            return ProductPriceResponse(
                success=True,
                prices=prices
            )
    except Exception as e:
        return ProductPriceResponse(success=False, error=str(e))


# ----- Payment Tools -----

class PaymentMethodResponse(BaseModel):
    """Response model for payment method operations"""

    success: bool = Field(description="Indicates if the operation was successful")
    payment_methods: Optional[List[Dict[str, Any]]] = Field(None, description="List of available payment methods")
    error: Optional[str] = Field(None, description="Error message, if any")


@mcp.tool(description="Get available payment methods")
def get_payment_methods(
    ctx: Context,
    partner_id: Optional[int] = None,
    company_id: Optional[int] = None,
    active_only: bool = True,
) -> PaymentMethodResponse:
    """
    Get available payment methods

    Parameters:
        partner_id: Customer/partner ID (optional, filters methods available to this partner)
        company_id: Company ID (optional, filters methods for this company)
        active_only: Whether to include only active payment methods (default: True)

    Returns:
        PaymentMethodResponse containing the payment methods
    """
    odoo = ctx.request_context.lifespan_context.odoo

    try:
        # Build domain
        domain = []

        # Add active filter if requested
        if active_only:
            domain.append(('active', '=', True))

        # Add company filter if provided
        if company_id:
            domain.append(('company_id', 'in', [company_id, False]))

        # Get payment methods
        payment_methods = odoo.search_read(
            model_name='account.payment.method',
            domain=domain,
            fields=['id', 'name', 'code', 'payment_type']
        )

        # If partner_id is provided, filter methods based on partner settings
        if partner_id and payment_methods:
            partner = odoo.read_records('res.partner', [partner_id], ['property_payment_method_id'])
            if partner and partner[0]['property_payment_method_id']:
                # Highlight the partner's preferred payment method
                preferred_method_id = partner[0]['property_payment_method_id'][0]
                for method in payment_methods:
                    method['is_preferred'] = (method['id'] == preferred_method_id)

        return PaymentMethodResponse(
            success=True,
            payment_methods=payment_methods
        )
    except Exception as e:
        return PaymentMethodResponse(success=False, error=str(e))


# ----- Vector Service Integration Tools -----


def get_product_metadata(odoo: OdooClient, account_id: str, product_id: int) -> Dict[str, Any]:
    """
    Get product metadata for description generation.

    Args:
        odoo: Odoo client
        account_id: Account ID
        product_id: Product ID

    Returns:
        Dict with product metadata
    """
    try:
        # Log the request for debugging
        print(f"Getting metadata for product {product_id} in account {account_id}")

        # Get basic product data
        product_data = odoo.execute(
            'product.template',
            'read',
            [product_id],
            ['name', 'categ_id', 'description_sale', 'description']
        )[0]

        # Get category name
        category = {}
        if product_data.get('categ_id'):
            category = odoo.execute(
                'product.category',
                'read',
                [product_data['categ_id'][0]],
                ['name']
            )[0]

        # Get attributes and values
        attribute_lines = odoo.execute(
            'product.template.attribute.line',
            'search_read',
            [('product_tmpl_id', '=', product_id)],
            ['attribute_id', 'value_ids']
        )

        attributes = []
        for attr_line in attribute_lines:
            attr_values = []
            if attr_line.get('value_ids'):
                attr_values = odoo.execute(
                    'product.attribute.value',
                    'read',
                    attr_line['value_ids'],
                    ['name']
                )
                attr_values = [v['name'] for v in attr_values]

            attributes.append({
                'name': attr_line['attribute_id'][1],
                'values': attr_values
            })

        # Get semantic description fields if available
        semantic_fields = odoo.execute(
            'product.template',
            'read',
            [product_id],
            ['semantic_description', 'key_features', 'use_cases', 'ai_generated_description', 'semantic_description_verified']
        )[0]

        # Prepare metadata
        metadata = {
            'id': product_id,
            'name': product_data.get('name', ''),
            'category': category.get('name', ''),
            'description_sale': product_data.get('description_sale', ''),
            'description': product_data.get('description', ''),
            'attributes': attributes,
            'semantic_description': semantic_fields.get('semantic_description', ''),
            'key_features': semantic_fields.get('key_features', ''),
            'use_cases': semantic_fields.get('use_cases', ''),
            'ai_generated_description': semantic_fields.get('ai_generated_description', ''),
            'verified': semantic_fields.get('semantic_description_verified', False)
        }

        return metadata
    except Exception as e:
        raise Exception(f"Error getting product metadata: {str(e)}")


@mcp.tool(
    "generate_product_description",
    description="Generate a rich commercial description for a product based on its metadata",
)
def generate_product_description(
    ctx: Context, request: ProductDescriptionRequest
) -> ProductDescriptionResponse:
    """
    Generate a rich commercial description for a product based on its metadata

    This tool uses an LLM to create compelling product descriptions that can be
    reviewed and edited by users before being used for semantic search.
    """
    try:
        # Get Odoo client from context
        odoo = ctx.app.odoo

        # Get product metadata
        product_metadata = get_product_metadata(odoo, request.account_id, request.product_id)

        # Import the description agent
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from src.agents.product_description_agent import ProductDescriptionAgent

        # Initialize the description agent
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return ProductDescriptionResponse(
                success=False,
                error="OpenAI API key not configured"
            )

        description_agent = ProductDescriptionAgent(api_key)

        # Generate description
        description = description_agent.generate_description(product_metadata)

        return ProductDescriptionResponse(
            success=True,
            description=description,
            product_id=request.product_id
        )
    except Exception as e:
        return ProductDescriptionResponse(
            success=False,
            error=f"Error generating description: {str(e)}"
        )


@mcp.tool(
    "sync_product_to_vector_db",
    description="Synchronize a product to the vector database",
)
def sync_product_to_vector_db(
    ctx: Context, request: SyncProductRequest
) -> SyncProductResponse:
    """
    Synchronize a product to the vector database for semantic search

    This tool generates embeddings and stores them in Qdrant for semantic search.
    """
    try:
        # Get Odoo client from context
        odoo = ctx.app.odoo

        # Get product data from Odoo if description not provided
        description = request.description
        product_data = {}

        if not description:
            product_data = get_product_metadata(odoo, request.account_id, request.product_id)
            description = product_data.get('ai_generated_description') or product_data.get('semantic_description')

        if not description:
            return SyncProductResponse(
                success=False,
                error="No description available for vectorization"
            )

        # Prepare metadata
        if not product_data:
            product_data = get_product_metadata(odoo, request.account_id, request.product_id)

        metadata = {
            "product_id": request.product_id,
            "name": product_data.get("name", ""),
            "category": product_data.get("category", ""),
            "verified": product_data.get("verified", True)
        }

        # Call Vector Service API
        vector_service_url = os.environ.get("VECTOR_SERVICE_URL", "http://localhost:8001")

        response = requests.post(
            f"{vector_service_url}/api/v1/vectors",
            json={
                "account_id": request.account_id,
                "product_id": str(request.product_id),
                "text": description,
                "metadata": metadata
            }
        )

        if response.status_code != 201:
            return SyncProductResponse(
                success=False,
                error=f"Vector Service error: {response.text}"
            )

        result = response.json()

        # Update product in Odoo with vector ID and sync status if needed
        if not request.skip_odoo_update:
            odoo.execute(
                'product.template',
                'write',
                [request.product_id],
                {
                    'semantic_vector_id': result.get("vector_id"),
                    'semantic_sync_status': 'synced'
                }
            )

        return SyncProductResponse(
            success=True,
            vector_id=result.get("vector_id"),
            message="Product successfully synchronized with vector database"
        )
    except Exception as e:
        return SyncProductResponse(
            success=False,
            error=f"Error synchronizing product: {str(e)}"
        )


@mcp.tool(
    "semantic_search",
    description="Perform semantic search for products",
)
def semantic_search(
    ctx: Context, request: SemanticSearchRequest
) -> SemanticSearchResponse:
    """
    Perform semantic search for products

    This tool searches for products using natural language queries.
    """
    try:
        # Call Vector Service API
        vector_service_url = os.environ.get("VECTOR_SERVICE_URL", "http://localhost:8001")

        response = requests.post(
            f"{vector_service_url}/api/v1/search",
            json={
                "account_id": request.account_id,
                "query": request.query,
                "limit": request.limit,
                "filter": request.filter
            }
        )

        if response.status_code != 200:
            return SemanticSearchResponse(
                success=False,
                error=f"Vector Service error: {response.text}"
            )

        result = response.json()

        # Enrich results with Odoo data if needed
        odoo = ctx.app.odoo
        enriched_results = []

        for item in result.get("results", []):
            product_id = item.get("metadata", {}).get("product_id")
            if product_id:
                try:
                    product_data = odoo.execute(
                        'product.template',
                        'read',
                        [int(product_id)],
                        ['name', 'list_price', 'image_1920']
                    )[0]

                    # Add product data to result
                    item["product_data"] = {
                        "name": product_data.get("name"),
                        "price": product_data.get("list_price"),
                        "has_image": bool(product_data.get("image_1920"))
                    }
                except Exception as e:
                    # If we can't get product data, just continue with the result as is
                    pass

            enriched_results.append(item)

        return SemanticSearchResponse(
            success=True,
            results=enriched_results,
            count=len(enriched_results)
        )
    except Exception as e:
        return SemanticSearchResponse(
            success=False,
            error=f"Error performing semantic search: {str(e)}"
        )


# ----- Product Metadata Tools -----

class ProductMetadataRequest(BaseModel):
    """Request model for product metadata"""
    product_id: int
    include_variants: bool = True
    include_attributes: bool = True
    include_images: bool = False
    include_categories: bool = True
    lang: str = "pt_BR"


class ProductAttributeValue(BaseModel):
    """Product attribute value"""
    id: int
    name: str


class ProductAttribute(BaseModel):
    """Product attribute"""
    id: int
    name: str
    values: List[ProductAttributeValue]


class ProductCategory(BaseModel):
    """Product category"""
    id: int
    name: str
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None


class ProductImage(BaseModel):
    """Product image"""
    id: int
    name: Optional[str] = None
    url: str


class ProductVariant(BaseModel):
    """Product variant"""
    id: int
    name: str
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    list_price: float
    attributes: Dict[str, str] = Field(default_factory=dict)


class ProductMetadata(BaseModel):
    """Complete product metadata"""
    product_id: int
    name: str
    description: Optional[str] = None
    description_sale: Optional[str] = None
    categ_id: Optional[int] = None
    categ_name: Optional[str] = None
    list_price: Optional[float] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    active: bool = True
    sale_ok: bool = True
    purchase_ok: bool = True
    type: str = "product"
    category: Optional[ProductCategory] = None
    attributes: List[ProductAttribute] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)
    images: List[ProductImage] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


@mcp.tool(
    "get_product_metadata",
    description="Get detailed product metadata including variants, attributes, and categories",
)
def get_product_metadata(ctx: Context, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed product metadata from Odoo.

    This tool retrieves comprehensive product information including variants,
    attributes, categories, and images if requested.
    """
    try:
        # Get Odoo client from context
        odoo = ctx.app.odoo

        # Parse request
        req = ProductMetadataRequest(**request)
        product_id = req.product_id

        # Get basic product data
        product_data = odoo.execute(
            'product.template',
            'read',
            [product_id],
            [
                'name', 'description', 'description_sale', 'categ_id',
                'list_price', 'default_code', 'barcode', 'active',
                'sale_ok', 'purchase_ok', 'type'
            ]
        )

        if not product_data:
            return {
                "success": False,
                "error": f"Product with ID {product_id} not found"
            }

        product_data = product_data[0]

        # Initialize metadata
        metadata = ProductMetadata(
            product_id=product_id,
            name=product_data.get('name', ''),
            description=product_data.get('description', ''),
            description_sale=product_data.get('description_sale', ''),
            categ_id=product_data.get('categ_id', [False, ''])[0] if product_data.get('categ_id') else None,
            categ_name=product_data.get('categ_id', [False, ''])[1] if product_data.get('categ_id') else None,
            list_price=product_data.get('list_price', 0.0),
            default_code=product_data.get('default_code', ''),
            barcode=product_data.get('barcode', ''),
            active=product_data.get('active', True),
            sale_ok=product_data.get('sale_ok', True),
            purchase_ok=product_data.get('purchase_ok', True),
            type=product_data.get('type', 'product')
        )

        # Get category data if requested
        if req.include_categories and metadata.categ_id:
            category_data = odoo.execute(
                'product.category',
                'read',
                [metadata.categ_id],
                ['name', 'parent_id']
            )

            if category_data:
                category = category_data[0]
                parent_id = None
                parent_name = None

                if category.get('parent_id'):
                    parent_id = category['parent_id'][0]
                    parent_name = category['parent_id'][1]

                metadata.category = ProductCategory(
                    id=metadata.categ_id,
                    name=category.get('name', ''),
                    parent_id=parent_id,
                    parent_name=parent_name
                )

        # Get product attributes if requested
        if req.include_attributes:
            # Get attribute lines
            attr_lines = odoo.execute(
                'product.template.attribute.line',
                'search_read',
                [('product_tmpl_id', '=', product_id)],
                ['attribute_id', 'value_ids']
            )

            attributes = []
            for line in attr_lines:
                attr_id = line['attribute_id'][0]
                attr_name = line['attribute_id'][1]
                value_ids = line['value_ids']

                # Get attribute values
                if value_ids:
                    values_data = odoo.execute(
                        'product.attribute.value',
                        'read',
                        value_ids,
                        ['name']
                    )

                    values = [
                        ProductAttributeValue(id=val['id'], name=val['name'])
                        for val in values_data
                    ]

                    attributes.append(ProductAttribute(
                        id=attr_id,
                        name=attr_name,
                        values=values
                    ))

            metadata.attributes = attributes

        # Get product variants if requested
        if req.include_variants:
            # Get product variants
            variant_ids = odoo.execute(
                'product.product',
                'search',
                [('product_tmpl_id', '=', product_id)]
            )

            if variant_ids:
                variants_data = odoo.execute(
                    'product.product',
                    'read',
                    variant_ids,
                    ['name', 'default_code', 'barcode', 'list_price']
                )

                variants = []
                for variant in variants_data:
                    # Get variant attributes
                    variant_attrs = {}
                    attr_vals = odoo.execute(
                        'product.template.attribute.value',
                        'search_read',
                        [('product_id', '=', variant['id'])],
                        ['attribute_id', 'name']
                    )

                    for attr_val in attr_vals:
                        attr_name = attr_val['attribute_id'][1]
                        variant_attrs[attr_name] = attr_val['name']

                    variants.append(ProductVariant(
                        id=variant['id'],
                        name=variant['name'],
                        default_code=variant.get('default_code', ''),
                        barcode=variant.get('barcode', ''),
                        list_price=variant.get('list_price', 0.0),
                        attributes=variant_attrs
                    ))

                metadata.variants = variants

        # Get product images if requested
        if req.include_images:
            # Get product images
            image_ids = odoo.execute(
                'product.image',
                'search',
                [('product_tmpl_id', '=', product_id)]
            )

            if image_ids:
                images_data = odoo.execute(
                    'product.image',
                    'read',
                    image_ids,
                    ['name']
                )

                base_url = odoo.get_base_url()
                images = []

                for image in images_data:
                    image_url = f"{base_url}/web/image/product.image/{image['id']}/image_1920"
                    images.append(ProductImage(
                        id=image['id'],
                        name=image.get('name', ''),
                        url=image_url
                    ))

                # Add main product image
                main_image_url = f"{base_url}/web/image/product.template/{product_id}/image_1920"
                images.insert(0, ProductImage(
                    id=0,
                    name="Main Image",
                    url=main_image_url
                ))

                metadata.images = images

        # Return metadata
        return {
            "success": True,
            "metadata": metadata.dict()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool(
    "search_products_semantic",
    description="Search products with semantic relevance and filtering",
)
def search_products_semantic(ctx: Context, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for products with semantic relevance and filtering.

    This tool combines traditional filtering with semantic search capabilities,
    allowing for more natural language queries while still respecting hard filters.
    """
    try:
        # Get Odoo client from context
        odoo = ctx.app.odoo

        # Extract parameters
        query = request.get("query", "")
        filters = request.get("filters", [])
        limit = request.get("limit", 10)
        offset = request.get("offset", 0)
        fields = request.get("fields", [
            "id", "name", "description", "description_sale",
            "list_price", "default_code", "categ_id"
        ])

        # Ensure id is always included
        if "id" not in fields:
            fields.append("id")

        # Build domain
        domain = [
            ("active", "=", True),
            ("sale_ok", "=", True)
        ]

        # Add custom filters
        if filters:
            domain.extend(filters)

        # If query is provided, add basic text search
        # Note: This is a simple implementation. In a real system,
        # this would be integrated with the vector search service.
        if query:
            domain.append("|")  # OR operator
            domain.append(("name", "ilike", query))
            domain.append(("description", "ilike", query))

        # Search for products
        product_ids = odoo.execute(
            "product.template",
            "search",
            domain,
            limit=limit,
            offset=offset
        )

        if not product_ids:
            return {
                "success": True,
                "products": [],
                "total": 0
            }

        # Read product data
        products = odoo.execute(
            "product.template",
            "read",
            product_ids,
            fields
        )

        # Get total count (without limit/offset)
        total_count = odoo.execute(
            "product.template",
            "search_count",
            domain
        )

        return {
            "success": True,
            "products": products,
            "total": total_count
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

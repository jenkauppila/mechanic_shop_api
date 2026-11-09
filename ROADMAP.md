# Roadmap

The next major feature for Mechanic Shop API is stock control: tracking what the shop has, what is committed to service jobs, and what has already been used.

The initial scope is estimated at **25 to 35 hours**, including implementation, testing, and documentation. These are planning estimates and may change as the work is scoped.

## Before stock control: ticket access (Step 0)

Two open issues come first, because stock reservations happen on service tickets. They are not counted in the 25 to 35 hour estimate.

- [#8: Require login to create, edit, and delete service tickets](https://github.com/jenkauppila/mechanic_shop_api/issues/8), with ownership checks so a customer can only change their own tickets.
- [#10: Reject tickets where the vehicle belongs to a different customer](https://github.com/jenkauppila/mechanic_shop_api/issues/10)

## Open design question: guest access

This project is a public demo. The goal is to protect the back end while still letting visitors explore freely. How to do that is not decided yet. Options being considered:

- A one-click guest sign-in in a future front end that creates a throwaway demo customer behind the scenes. The API keeps its login and ownership checks, and visitors never see a login screen.
- A clear on-screen note that a real shop would require a login for these actions.
- A fictional demo staff account for admin-level actions.

The decision will be recorded here once it is made.

## Inventory quantities

- **On hand:** parts physically in the shop, including reserved parts.
- **Reserved:** parts committed to service tickets but not yet used.
- **Available:** on-hand quantity minus reserved quantity.
- **Used:** parts installed or consumed, which are no longer on hand.

For example, 12 oil filters on hand with 4 reserved leaves 8 available. When the 4 reserved filters are used, on hand drops to 8 and reserved drops to 0. Available remains 8.

## Planned work

### 1. Track stock and validate values (4 to 5 hours)

- Add whole-number stock quantities to inventory items.
- Add the new stock columns to the existing live database with a one-time SQL script, because the project has no migration tool.
- Default existing inventory items to zero stock and update demo data.
- Reject negative stock and negative prices.
- Require positive whole numbers when receiving, reserving, or using parts.
- Add database safeguards and tests for invalid values.

### 2. Receive and adjust inventory (4 to 6 hours)

- Record incoming deliveries and increase on-hand quantities.
- Support stock corrections with a recorded reason.
- Prevent adjustments that reduce on-hand stock below existing reservations.
- Keep a basic history of stock movements.
- Test receipts, corrections, and rejected adjustments.

### 3. Reserve parts for service tickets (6 to 8 hours)

- Reserve available parts when assigning them to a service ticket.
- Redefine the existing ticket item quantity, which currently means parts used, as reserved or used, and update the demo data to match.
- Support changing or canceling reservations.
- Reject reservations exceeding available stock.
- Prevent simultaneous requests from reserving the same remaining stock.
- Test availability calculations and competing reservations.

### 4. Record parts used (4 to 6 hours)

- Explicitly mark reserved parts as used.
- Reduce on-hand and reserved quantities together when parts are consumed.
- Support partial use and release unused reservations.
- Prevent repeated requests from deducting the same parts twice.
- Require reservations to be resolved before deleting a ticket, and preserve records of parts already used.
- Test the reserve, use, and release workflow.

### 5. Protect stock operations (4 to 6 hours)

- Add a minimal staff permission for receiving, adjusting, and consuming stock.
- Apply customer ownership checks to customer-facing ticket reservation operations.
- Prevent unauthorized inventory changes.
- Add permission tests and fictional demo staff accounts.

### 6. Add low-stock visibility and finish integration (3 to 4 hours)

- Add an optional minimum-available threshold for each inventory item.
- Provide an endpoint listing items below their threshold.
- Update API documentation and demo scenarios.
- Add end-to-end tests for receiving, reserving, and using stock.

For example, an oil filter with a minimum available quantity of 5 should be flagged when availability falls to 4, even if additional filters are physically present but reserved for other jobs.

The initial version will flag low stock without placing supplier orders.

## Related existing issues

These issues remain part of the backlog and support the stock-control work:

- [#9: Require login to update and delete inventory items](https://github.com/jenkauppila/mechanic_shop_api/issues/9)
- [#11: Add input validation](https://github.com/jenkauppila/mechanic_shop_api/issues/11)
- [#12: Add a staff/admin role and protect mechanic management](https://github.com/jenkauppila/mechanic_shop_api/issues/12)

The stock-control estimate includes only the parts of these issues that the stock work needs: stock and price validation from issue 11 (Phase 1) and the stock-related staff permission from issue 12 (Phase 5). It does not include completing every requirement in these issues. Each issue stays open until its full scope is implemented and verified.

## Possible later enhancements

- A simple front end where visitors can try changes and see their effect on the API without needing to know the code.
- Suggested reorder quantities.
- Draft purchase orders and supplier records.
- Delivery tracking.
- Automatic reordering with approval controls and duplicate-order prevention.

These enhancements are outside the initial 25 to 35 hour estimate.

## Housekeeping

- GET /customers is public and lists names, emails, and phone numbers. That is acceptable with fake demo data and should be revisited if real data is ever used.
- Known bugs are tracked in [docs/BUG_REPORT.md](docs/BUG_REPORT.md).

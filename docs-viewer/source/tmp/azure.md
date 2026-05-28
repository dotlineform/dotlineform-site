---
doc_id: azure
title: "azure"
added_date: 2026-05-28
last_updated: 2026-05-28
ui_status: draft
parent_id: ""
sort_order: 700
---


> you mention not creating a permissions framework, which is correct, we don't need one on the local host. but if in the future we wanted to host studio on, say, Azure static websites, we would need some kind of login. or could that just be handled by the azure login?

For a future hosted Studio, Azure can probably handle the login layer, but it would not replace all app-level authorization decisions.

Azure Static Web Apps has built-in authentication/authorization with providers like Microsoft Entra ID, and route rules can restrict pages to authenticated users or roles via `staticwebapp.config.json` ([Microsoft docs](https://learn.microsoft.com/en-us/azure/static-web-apps/add-authentication), [configuration docs](https://learn.microsoft.com/en-in/azure/static-web-apps/configuration)). So for “only I / only my tenant / only named users can open Studio,” Azure login is likely the right first layer.

But there are two separate concerns:

- **Access to the hosted Studio UI:** Azure/Entra can handle this well.
- **Authority to write, rebuild, import, edit metadata, touch source files, or access local/project storage:** the app/backend still needs explicit server-side validation.

So the current “don’t create a permissions framework” steer is still right for localhost. For hosted Studio, I’d frame it as a future deployment/auth boundary, not something this Docs Viewer public/manage context slice should build now.

If we ever host Studio remotely, the design should likely be:

- Azure/Entra gates access to the Studio route.
- Static/public Docs Viewer routes remain read-only.
- Any write-capable backend/API validates identity and allowed actions server-side.
- Browser route config still does not imply write authority.
- The frontend receives capabilities from the authenticated backend, not from static config alone.

So: yes, Azure login may cover the login experience, but it would not remove the need for backend capability checks if hosted Studio has write operations.

> and presumably the app architecture we are building would enable us to build a permissions framework easier than it would have been before?

Yes. The architecture we’re building should make a future permissions model much easier, even though we are deliberately not building one now.

The important improvements are:

- **Route context is separate from backend capability truth.** Static config can say “this route is manage-capable,” but write authority still has to come from a backend/service flow.
- **Public and manage contexts are being made explicit.** That gives a natural place to later add authenticated user/capability projection without scattering checks across feature modules.
- **Management writes already flow through management/service modules.** A future permission check can sit at the backend/API boundary and in the management capability response, instead of being inferred by UI state.
- **Returned runtime handles are smaller.** Feature modules have fewer escape hatches into broad state or service handles, so future permissions are less likely to be bypassed accidentally.
- **Service context is becoming a named owner.** That is the right place to distinguish public static reads, authenticated generated reads, and write-capable APIs.
- **Hosted views/controllers receive explicit inputs.** Future views can declare “public-safe,” “authenticated read,” or “manage-write” needs without depending on global runtime state.

So the practical answer is: this work does not implement permissions, but it creates the seams where permissions would belong later. Before these slices, a permissions framework would likely have been bolted onto broad runtime state and scattered mode checks. After these slices, it can be modeled as backend capability plus explicit app/service context.
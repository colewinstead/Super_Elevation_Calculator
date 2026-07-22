# MDOT transition profile model

## Scope and source record

This document records how calculation engine `1.2.1` turns the MDOT criteria values already calculated by `Super.py` into lane-by-lane, piecewise-linear transition profiles. It does not change the MDOT rate tables, relative-gradient tables, friction logic, station equations, coordinate transforms, or LandXML geometry.

The implementation was checked against these official MDOT sources:

- [*2020 Roadway Design Manual*](https://mdot.ms.gov/documents/Roadway%20Design/Standards/Manuals/2020%20Roadway%20Design%20Manual.pdf), Section 3-4.02, “Superelevation Transition,” including Sections 3-4.02.01 through 3-4.02.04 (manual pages 3-9 through 3-13; PDF pages 75 through 79).
- [*Roadway Design Standard Drawings*](https://mdot.ms.gov/documents/Roadway%20Design/Standards/Drawings/Roadway%20Design%20Standard%20Drawings.pdf), sheet SE-2A, “Superelevation Runoff – Minimum Radii & Limiting Values for e,” sheet 6408, issue date August 1, 2017.
- The same Standard Drawings compilation, sheet SE-3A, “Superelevation Runoff Case I,” sheet 6413, issue date August 1, 2017.

The selected criteria profile continues to identify the MDOT standard-drawing compilation revision as April 22, 2026. The individual SE-2A and SE-3A sheets carry the August 1, 2017 issue date.

## Simple circular curves

The lane profile is assembled once in `super_transition.py` and is consumed unchanged by the browser diagram, engineering lookup, PDF, ORD CSV, DXF, and corridor QA.

For a simple circular curve without spirals:

- Total transition consists of tangent runout `Lt` plus superelevation runoff `Lr`.
- Tangent runout changes the outside lane from normal crown to 0% cross slope.
- Runoff changes the roadway from the 0%/reverse-crown condition to full superelevation.
- Approximately 70% of `Lr` is placed before PC and 30% after PC. The exit is symmetric about PT.
- The outside lane changes linearly from 0% to full superelevation over `Lr`.
- The inside lane remains at normal crown until the SE-3A breakpoint `X1 = Lr(NC/e)`, then changes linearly to full superelevation.
- If `X1` falls after PC for a low rate, the profile labels that point `BEGIN ROTATION`; it does not mislabel it as the point of normal crown.

The engine records PC and PT as points sampled on these straight transition segments. They do not create an extra kink.

## Reverse curves with an intervening tangent

The standard manual requires enough tangent length for the transition between reverse curves but does not provide a separate reverse-curve diagram implementing the product-specific option below. The following rule is therefore a documented engineering rule supplied for this calculator and must be independently checked for project applicability:

`Tmin = 0.7Lr(exit) + 0.7Lr(entry)`

When two consecutive MDOT circular curves turn in opposite directions and reverse-curve coordination is selected:

- Tangent runout is omitted only between the two coordinated curves.
- At exactly `Tmin`, each curve retains its standard runoff length and normal 30%/70% placement at PT or PC.
- When the tangent is at least `Tmin`, the two runoff transitions are extended proportionally to meet at one shared 0% station. There is no level 0% segment.
- The shared station divides the tangent in proportion to `0.7Lr(exit)` and `0.7Lr(entry)`. It is the tangent midpoint when the two runoff lengths are equal.
- If the tangent is longer than `Tmin`, Corridor QA emits a review warning because the resulting transition rate is slower than the standard rate.
- If the tangent is shorter than `Tmin`, coordination is not applied. Corridor QA emits a blocking `SHORT_REVERSE_TANGENT` finding; the engine does not shorten or move either runoff to conceal the deficiency.
- Criteria profile, direction, or eligibility failures never cause a silent substitution or altered calculation.

For the sanitized `tests/fixtures/cw_reverse_curve.xml` regression at 65 mph, the tangent is 123.0 ft and `Tmin` is 86.1 ft. The two extended linear transitions meet at one 0% station and Corridor QA flags the slower-than-standard transition rate for review.

## Change control

Any future change to the equations, rate/runoff tables, 30%/70% placement, `X1` breakpoint, signs, stationing, or reverse-curve minimum rule requires renewed qualified roadway-engineer review and new versioned regression evidence.

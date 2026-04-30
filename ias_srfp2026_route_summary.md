# IAS SRFP 2026 Selected List Route Summary

Source page: https://webjapps.ias.ac.in/fellowship2026/lists/result1.jsp

Site data version: 2026-04-30

## Frontend Route

The result page does not embed selected candidate names in the frontend HTML.
It embeds counts and JavaScript subject links such as `javascript:submit('Lif')`.

The click handler sends:

```text
POST /fellowship2026/lists/sessionAjax.jsp?subject=<subject_code>
```

Then the browser is redirected to:

```text
GET /fellowship2026/lists/selectedList.jsp
```

## Backend Behavior

`sessionAjax.jsp` stores the selected subject in the JSP session and echoes the subject code.
`selectedList.jsp` renders the selected-candidate table server-side using that session value.

Conclusion: the candidate records are backend/server-rendered, not present as frontend data or a JSON route in the initial page.

## Subject Results

| Subject Code | Section | Route Result | Last Updated |
| --- | --- | --- | --- |
| Che | Chemistry | 72 selected candidates | 2026-04-30 |
| Eps | Earth and Planetary Sciences | 20 selected candidates | 2026-04-30 |
| Eng | Engineering including Computer Sciences | 247 selected candidates | 2026-04-30 |
| Lif | Life Sciences | 115 selected candidates | 2026-04-30 |
| Mat | Mathematics | 19 selected candidates | 2026-04-30 |
| Phy | Physics | 61 selected candidates | 2026-04-30 |

Total selected rows found: 534.

All selected people are saved in `ias_srfp2026_selected_people.csv`.

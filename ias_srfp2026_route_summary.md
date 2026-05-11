# IAS SRFP 2026 Selected List Route Summary

Source page: https://webjapps.ias.ac.in/fellowship2026/lists/result1.jsp

Site data version: 2026-05-11

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
| Che | Chemistry | 116 selected candidates | 2026-05-11 |
| Eps | Earth and Planetary Sciences | 28 selected candidates | 2026-05-11 |
| Eng | Engineering including Computer Sciences | 300 selected candidates | 2026-05-11 |
| Lif | Life Sciences | 191 selected candidates | 2026-05-11 |
| Mat | Mathematics | 25 selected candidates | 2026-05-11 |
| Phy | Physics | 95 selected candidates | 2026-05-11 |

Total selected rows found: 755.

All selected people are saved in `ias_srfp2026_selected_people.csv`.

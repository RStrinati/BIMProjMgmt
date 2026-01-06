USE ReviztoData;
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER VIEW [dbo].[vw_ReviztoProjectIssues_Deconstructed] AS
WITH Cleaned AS (
    SELECT
        issueId,
        projectUuid,
        TRY_CAST(issueJson AS NVARCHAR(MAX)) AS cleaned_json
    FROM dbo.tblReviztoProjectIssues
    WHERE ISJSON(issueJson) = 1
),
PositionProps AS (
    SELECT
        c.issueId,
        JSON_VALUE(c.cleaned_json, '$.positionProperties.value') AS position_properties_base64
    FROM Cleaned c
)
SELECT
    c.issueId,
    c.projectUuid,
    JSON_VALUE(c.cleaned_json, '$.uuid') AS uuid,
    JSON_VALUE(c.cleaned_json, '$.id') AS issue_number,
    JSON_VALUE(c.cleaned_json, '$.title.value') AS title,
    JSON_VALUE(c.cleaned_json, '$.status.value') AS status,
    JSON_VALUE(c.cleaned_json, '$.priority.value') AS priority,
    JSON_VALUE(c.cleaned_json, '$.created.value') AS created,
    JSON_VALUE(c.cleaned_json, '$.updated') AS updated,
    JSON_VALUE(c.cleaned_json, '$.author.firstname') AS author_firstname,
    JSON_VALUE(c.cleaned_json, '$.author.email') AS author_email,
    JSON_VALUE(c.cleaned_json, '$.assignee.value') AS assignee_email,
    JSON_VALUE(c.cleaned_json, '$.openLinks.web') AS web_link,
    JSON_VALUE(c.cleaned_json, '$.preview.middle') AS preview_middle_url,
    JSON_QUERY(c.cleaned_json, '$.tags.value') AS tags_json,
    pp.position_properties_base64 AS position_properties_raw,
    CASE
        WHEN pp.position_properties_base64 IS NULL THEN NULL
        ELSE TRY_CONVERT(
            NVARCHAR(255),
            CAST('' AS XML).value(
                'xs:base64Binary(sql:column("pp.position_properties_base64"))',
                'varbinary(max)'
            )
        )
    END AS position_properties_decoded,
    p.title AS project_title,
    p.region,
    JSON_VALUE(CAST(p.projectJson AS NVARCHAR(MAX)), '$.preview') AS project_preview,
    JSON_VALUE(CAST(p.projectJson AS NVARCHAR(MAX)), '$.owner.fullname') AS owner_name
FROM Cleaned c
LEFT JOIN dbo.tblReviztoProjects p ON c.projectUuid = p.projectUuid
LEFT JOIN PositionProps pp ON pp.issueId = c.issueId
WHERE ISJSON(c.cleaned_json) = 1;
GO

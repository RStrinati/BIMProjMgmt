const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

// Database helper using sqlcmd since direct connection isn't working
class DatabaseHelper {
    constructor() {
        this.connectionString = 'P-NB-USER-028\\SQLEXPRESS';
        this.username = 'admin02';
        this.password = '1234';
        this.database = 'acc_data_schema';
    }

    async executeQuery(query) {
        try {
            // Escape quotes in the query
            const escapedQuery = query.replace(/'/g, "''");
            
            const command = `sqlcmd -S "${this.connectionString}" -U ${this.username} -P ${this.password} -d ${this.database} -Q "${escapedQuery}" -h -1 -s "," -W`;
            
            console.log('🔍 Executing SQL query via sqlcmd...');
            const { stdout, stderr } = await execAsync(command);
            
            if (stderr) {
                console.error('SQL Error:', stderr);
                throw new Error(stderr);
            }
            
            // Parse CSV-like output
            const lines = stdout.trim().split('\n');
            if (lines.length === 0) return [];
            
            // Skip empty lines and parse data
            const dataLines = lines.filter(line => line.trim() !== '');
            const result = [];
            
            for (const line of dataLines) {
                const values = line.split(',').map(val => val.trim());
                result.push(values);
            }
            
            return result;
        } catch (error) {
            console.error('Database query failed:', error.message);
            throw error;
        }
    }

    async executeNonQuery(query) {
        try {
            const escapedQuery = query.replace(/'/g, "''");
            const command = `sqlcmd -S "${this.connectionString}" -U ${this.username} -P ${this.password} -d ${this.database} -Q "${escapedQuery}"`;
            
            console.log('💾 Executing SQL command via sqlcmd...');
            const { stdout, stderr } = await execAsync(command);
            
            if (stderr) {
                console.error('SQL Error:', stderr);
                throw new Error(stderr);
            }
            
            return stdout;
        } catch (error) {
            console.error('Database command failed:', error.message);
            throw error;
        }
    }

    async testConnection() {
        try {
            console.log('🧪 Testing database connection...');
            const result = await this.executeQuery('SELECT GETDATE() as CurrentTime, @@SERVERNAME as ServerName, DB_NAME() as DatabaseName');
            console.log('✅ Database connection successful!');
            console.log('Connection details:', result[0]);
            return true;
        } catch (error) {
            console.error('❌ Database connection failed:', error.message);
            return false;
        }
    }

    async getProjectCount() {
        try {
            const result = await this.executeQuery('SELECT COUNT(*) as count FROM admin_projects');
            return parseInt(result[0][0]);
        } catch (error) {
            console.error('Failed to get project count:', error.message);
            return 0;
        }
    }

    async insertProject(projectData) {
        try {
            const { id, name, status, account_id } = projectData;
            const query = `
                INSERT INTO admin_projects (id, name, status, account_id, created_at, updated_at)
                VALUES ('${id}', '${name.replace(/'/g, "''")}', '${status}', '${account_id}', GETDATE(), GETDATE())
            `;
            await this.executeNonQuery(query);
            console.log('✅ Project inserted successfully');
        } catch (error) {
            console.error('Failed to insert project:', error.message);
            throw error;
        }
    }

    async updateProject(projectData) {
        try {
            const { id, name, status } = projectData;
            const query = `
                UPDATE admin_projects 
                SET name = '${name.replace(/'/g, "''")}', 
                    status = '${status}', 
                    updated_at = GETDATE()
                WHERE id = '${id}'
            `;
            await this.executeNonQuery(query);
            console.log('✅ Project updated successfully');
        } catch (error) {
            console.error('Failed to update project:', error.message);
            throw error;
        }
    }

    async insertIssue(issueData) {
        try {
            const { id, title, status, project_id, assigned_to } = issueData;
            const query = `
                INSERT INTO issues_issues (id, title, status, project_id, assigned_to, created_at, updated_at)
                VALUES ('${id}', '${title.replace(/'/g, "''")}', '${status}', '${project_id}', '${assigned_to || ''}', GETDATE(), GETDATE())
            `;
            await this.executeNonQuery(query);
            console.log('✅ Issue inserted successfully');
        } catch (error) {
            console.error('Failed to insert issue:', error.message);
            throw error;
        }
    }

    async insertOrUpdateIssue(issueData) {
        try {
            const safeString = (value) => value ? `'${value.toString().replace(/'/g, "''")}'` : 'NULL';
            const safeDate = (value) => value ? `'${value}'` : 'NULL';
            const safeBit = (value) => value ? '1' : '0';

            const query = `
                IF EXISTS (SELECT 1 FROM issues_issues WHERE issue_id = ${safeString(issueData.issue_id)})
                    UPDATE issues_issues SET
                        bim360_account_id = ${safeString(issueData.bim360_account_id)},
                        bim360_project_id = ${safeString(issueData.bim360_project_id)},
                        display_id = ${issueData.display_id || 'NULL'},
                        title = ${safeString(issueData.title)},
                        description = ${safeString(issueData.description)},
                        type_id = ${safeString(issueData.type_id)},
                        subtype_id = ${safeString(issueData.subtype_id)},
                        status = ${safeString(issueData.status)},
                        assignee_id = ${safeString(issueData.assignee_id)},
                        assignee_type = ${safeString(issueData.assignee_type)},
                        due_date = ${safeDate(issueData.due_date)},
                        location_id = ${safeString(issueData.location_id)},
                        location_details = ${safeString(issueData.location_details)},
                        linked_document_urn = ${safeString(issueData.linked_document_urn)},
                        owner_id = ${safeString(issueData.owner_id)},
                        root_cause_id = ${safeString(issueData.root_cause_id)},
                        root_cause_category_id = ${safeString(issueData.root_cause_category_id)},
                        response = ${safeString(issueData.response)},
                        response_by = ${safeString(issueData.response_by)},
                        response_at = ${safeDate(issueData.response_at)},
                        opened_by = ${safeString(issueData.opened_by)},
                        opened_at = ${safeDate(issueData.opened_at)},
                        closed_by = ${safeString(issueData.closed_by)},
                        closed_at = ${safeDate(issueData.closed_at)},
                        created_by = ${safeString(issueData.created_by)},
                        created_at = ${safeDate(issueData.created_at)},
                        updated_by = ${safeString(issueData.updated_by)},
                        updated_at = ${safeDate(issueData.updated_at)},
                        start_date = ${safeDate(issueData.start_date)},
                        deleted_at = ${safeDate(issueData.deleted_at)},
                        snapshot_urn = ${safeString(issueData.snapshot_urn)},
                        published = ${safeBit(issueData.published)},
                        gps_coordinates = ${safeString(issueData.gps_coordinates)},
                        deleted_by = ${safeString(issueData.deleted_by)}
                    WHERE issue_id = ${safeString(issueData.issue_id)}
                ELSE
                    INSERT INTO issues_issues (
                        issue_id, bim360_account_id, bim360_project_id, display_id, title, description,
                        type_id, subtype_id, status, assignee_id, assignee_type, due_date, location_id,
                        location_details, linked_document_urn, owner_id, root_cause_id, root_cause_category_id,
                        response, response_by, response_at, opened_by, opened_at, closed_by, closed_at,
                        created_by, created_at, updated_by, updated_at, start_date, deleted_at,
                        snapshot_urn, published, gps_coordinates, deleted_by
                    ) VALUES (
                        ${safeString(issueData.issue_id)}, ${safeString(issueData.bim360_account_id)},
                        ${safeString(issueData.bim360_project_id)}, ${issueData.display_id || 'NULL'},
                        ${safeString(issueData.title)}, ${safeString(issueData.description)},
                        ${safeString(issueData.type_id)}, ${safeString(issueData.subtype_id)},
                        ${safeString(issueData.status)}, ${safeString(issueData.assignee_id)},
                        ${safeString(issueData.assignee_type)}, ${safeDate(issueData.due_date)},
                        ${safeString(issueData.location_id)}, ${safeString(issueData.location_details)},
                        ${safeString(issueData.linked_document_urn)}, ${safeString(issueData.owner_id)},
                        ${safeString(issueData.root_cause_id)}, ${safeString(issueData.root_cause_category_id)},
                        ${safeString(issueData.response)}, ${safeString(issueData.response_by)},
                        ${safeDate(issueData.response_at)}, ${safeString(issueData.opened_by)},
                        ${safeDate(issueData.opened_at)}, ${safeString(issueData.closed_by)},
                        ${safeDate(issueData.closed_at)}, ${safeString(issueData.created_by)},
                        ${safeDate(issueData.created_at)}, ${safeString(issueData.updated_by)},
                        ${safeDate(issueData.updated_at)}, ${safeDate(issueData.start_date)},
                        ${safeDate(issueData.deleted_at)}, ${safeString(issueData.snapshot_urn)},
                        ${safeBit(issueData.published)}, ${safeString(issueData.gps_coordinates)},
                        ${safeString(issueData.deleted_by)}
                    )
            `;
            
            await this.executeNonQuery(query);
            console.log('✅ Issue upserted successfully');
        } catch (error) {
            console.error('Failed to upsert issue:', error.message);
            throw error;
        }
    }

    async insertOrUpdateProjectDetailed(projectData) {
        try {
            const safeString = (value) => value ? `'${value.toString().replace(/'/g, "''")}'` : 'NULL';
            const safeDate = (value) => value ? `'${value}'` : 'NULL';
            const safeNumber = (value) => value ? value : 'NULL';
            const safeBit = (value) => value ? '1' : '0';

            const query = `
                IF EXISTS (SELECT 1 FROM admin_projects WHERE id = ${safeString(projectData.id)})
                    UPDATE admin_projects SET
                        bim360_account_id = ${safeString(projectData.bim360_account_id)},
                        name = ${safeString(projectData.name)},
                        start_date = ${safeDate(projectData.start_date)},
                        end_date = ${safeDate(projectData.end_date)},
                        type = ${safeString(projectData.type)},
                        value = ${safeNumber(projectData.value)},
                        currency = ${safeString(projectData.currency)},
                        status = ${safeString(projectData.status)},
                        job_number = ${safeString(projectData.job_number)},
                        address_line1 = ${safeString(projectData.address_line1)},
                        address_line2 = ${safeString(projectData.address_line2)},
                        city = ${safeString(projectData.city)},
                        state_or_province = ${safeString(projectData.state_or_province)},
                        postal_code = ${safeString(projectData.postal_code)},
                        country = ${safeString(projectData.country)},
                        timezone = ${safeString(projectData.timezone)},
                        construction_type = ${safeString(projectData.construction_type)},
                        contract_type = ${safeString(projectData.contract_type)},
                        business_unit_id = ${safeString(projectData.business_unit_id)},
                        last_sign_in = ${safeDate(projectData.last_sign_in)},
                        created_at = ${safeDate(projectData.created_at)},
                        acc_project = ${safeBit(projectData.acc_project)},
                        latitude = ${safeNumber(projectData.latitude)},
                        longitude = ${safeNumber(projectData.longitude)},
                        updated_at = GETDATE(),
                        status_reason = ${safeString(projectData.status_reason)},
                        total_member_size = ${safeNumber(projectData.total_member_size)},
                        total_company_size = ${safeNumber(projectData.total_company_size)},
                        classification = ${safeString(projectData.classification)}
                    WHERE id = ${safeString(projectData.id)}
                ELSE
                    INSERT INTO admin_projects (
                        id, bim360_account_id, name, start_date, end_date, type, value, currency,
                        status, job_number, address_line1, address_line2, city, state_or_province,
                        postal_code, country, timezone, construction_type, contract_type,
                        business_unit_id, last_sign_in, created_at, acc_project, latitude,
                        longitude, updated_at, status_reason, total_member_size, total_company_size,
                        classification
                    ) VALUES (
                        ${safeString(projectData.id)}, ${safeString(projectData.bim360_account_id)},
                        ${safeString(projectData.name)}, ${safeDate(projectData.start_date)},
                        ${safeDate(projectData.end_date)}, ${safeString(projectData.type)},
                        ${safeNumber(projectData.value)}, ${safeString(projectData.currency)},
                        ${safeString(projectData.status)}, ${safeString(projectData.job_number)},
                        ${safeString(projectData.address_line1)}, ${safeString(projectData.address_line2)},
                        ${safeString(projectData.city)}, ${safeString(projectData.state_or_province)},
                        ${safeString(projectData.postal_code)}, ${safeString(projectData.country)},
                        ${safeString(projectData.timezone)}, ${safeString(projectData.construction_type)},
                        ${safeString(projectData.contract_type)}, ${safeString(projectData.business_unit_id)},
                        ${safeDate(projectData.last_sign_in)}, ${safeDate(projectData.created_at)},
                        ${safeBit(projectData.acc_project)}, ${safeNumber(projectData.latitude)},
                        ${safeNumber(projectData.longitude)}, GETDATE(), ${safeString(projectData.status_reason)},
                        ${safeNumber(projectData.total_member_size)}, ${safeNumber(projectData.total_company_size)},
                        ${safeString(projectData.classification)}
                    )
            `;
            
            await this.executeNonQuery(query);
            console.log('✅ Project detailed upserted successfully');
        } catch (error) {
            console.error('Failed to upsert detailed project:', error.message);
            throw error;
        }
    }

    async getIssuesCount() {
        try {
            const result = await this.executeQuery('SELECT COUNT(*) as count FROM issues_issues');
            return parseInt(result[0][0]);
        } catch (error) {
            console.error('Failed to get issues count:', error.message);
            return 0;
        }
    }
}

module.exports = DatabaseHelper;
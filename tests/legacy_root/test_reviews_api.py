import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

# Test service reviews API
def test_service_reviews_api():
    base_url = 'http://localhost:5000'

    # First get a project with services
    try:
        response = requests.get(f'{base_url}/api/projects')
        if response.status_code != 200:
            print(f'Failed to get projects: {response.status_code}')
            return

        projects = response.json()
        if not projects:
            print('No projects found')
            return

        project_id = projects[0]['project_id']
        print(f'Testing with project {project_id}')

        # Get services for this project
        response = requests.get(f'{base_url}/api/projects/{project_id}/services')
        if response.status_code != 200:
            print(f'Failed to get services: {response.status_code}')
            return

        services = response.json()
        if not services:
            print('No services found for this project')
            return

        service_id = services[0]['service_id']
        print(f'Testing with service {service_id}')

        # Test service reviews endpoint
        response = requests.get(f'{base_url}/api/projects/{project_id}/services/{service_id}/reviews')
        print(f'Service reviews API status: {response.status_code}')
        if response.status_code == 200:
            reviews = response.json()
            print(f'Found {len(reviews)} reviews')
        else:
            print(f'Error: {response.text}')

    except Exception as e:
        print(f'Error testing API: {e}')

if __name__ == '__main__':
    test_service_reviews_api()
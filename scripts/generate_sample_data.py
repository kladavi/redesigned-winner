"""
Sample Data Generator
Creates sample incident data for testing the analyzer.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_servicenow_incidents(num_records: int = 500) -> pd.DataFrame:
    """Generate sample ServiceNow incident data."""
    
    # Base timestamp
    base_date = datetime(2025, 1, 1)
    
    # Sample data pools
    categories = ['Network', 'Hardware', 'Software', 'Database', 'Security', 'Cloud']
    subcategories = {
        'Network': ['Connectivity', 'Firewall', 'DNS', 'Load Balancer'],
        'Hardware': ['Server', 'Storage', 'Memory', 'CPU'],
        'Software': ['Application', 'OS', 'Update', 'License'],
        'Database': ['Performance', 'Connection', 'Backup', 'Replication'],
        'Security': ['Access', 'Vulnerability', 'Compliance', 'Breach'],
        'Cloud': ['AWS', 'Azure', 'GCP', 'Kubernetes']
    }
    
    priorities = ['1 - Critical', '2 - High', '3 - Medium', '4 - Low']
    priority_weights = [0.05, 0.15, 0.50, 0.30]
    
    states = ['New', 'In Progress', 'On Hold', 'Resolved', 'Closed']
    state_weights = [0.1, 0.15, 0.05, 0.30, 0.40]
    
    assignment_groups = ['Network Team', 'Server Team', 'DBA Team', 'Security Team', 
                        'Cloud Ops', 'Application Support', 'Level 2 Support']
    
    services = ['Web Portal', 'API Gateway', 'Payment System', 'User Database',
               'Email Service', 'Authentication', 'Reporting', 'Analytics']
    
    records = []
    for i in range(num_records):
        # Create incident number
        inc_num = f'INC{str(i + 1000001).zfill(7)}'
        
        # Random timestamps
        created = base_date + timedelta(
            days=random.randint(0, 60),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        state = random.choices(states, weights=state_weights)[0]
        
        # Resolved time only for resolved/closed incidents
        resolved = None
        if state in ['Resolved', 'Closed']:
            resolved = created + timedelta(
                hours=random.randint(1, 72),
                minutes=random.randint(0, 59)
            )
        
        category = random.choice(categories)
        
        record = {
            'number': inc_num,
            'sys_id': f'{i:032x}',
            'short_description': f'{category} issue - {random.choice(subcategories[category])} problem detected',
            'description': f'Detailed description of the {category.lower()} incident affecting services.',
            'category': category,
            'subcategory': random.choice(subcategories[category]),
            'priority': random.choices(priorities, weights=priority_weights)[0],
            'state': state,
            'impact': random.choice(['1 - High', '2 - Medium', '3 - Low']),
            'urgency': random.choice(['1 - High', '2 - Medium', '3 - Low']),
            'assignment_group': random.choice(assignment_groups),
            'assigned_to': f'user{random.randint(1, 50)}@company.com' if random.random() > 0.2 else None,
            'caller_id': f'caller{random.randint(1, 200)}@company.com',
            'cmdb_ci': random.choice(services),
            'sys_created_on': created.strftime('%Y-%m-%d %H:%M:%S'),
            'sys_updated_on': (created + timedelta(hours=random.randint(0, 24))).strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_at': resolved.strftime('%Y-%m-%d %H:%M:%S') if resolved else None,
            'closed_at': resolved.strftime('%Y-%m-%d %H:%M:%S') if state == 'Closed' and resolved else None,
        }
        records.append(record)
    
    # Add some duplicates for quality testing
    for _ in range(int(num_records * 0.02)):
        records.append(records[random.randint(0, len(records)-1)].copy())
    
    return pd.DataFrame(records)


def generate_newrelic_alerts(num_records: int = 500) -> pd.DataFrame:
    """Generate sample NewRelic alert data."""
    
    base_date = datetime(2025, 1, 1)
    
    policies = ['Production Alerts', 'Staging Alerts', 'Database Monitoring', 
               'API Performance', 'Infrastructure', 'Security Monitoring']
    
    conditions = ['High Error Rate', 'Slow Response Time', 'Memory Usage', 
                 'CPU Threshold', 'Disk Space', 'Connection Pool', 'Queue Depth']
    
    entities = ['web-server-01', 'web-server-02', 'api-gateway', 'db-primary',
               'db-replica', 'cache-01', 'queue-worker', 'load-balancer']
    
    severities = ['critical', 'warning', 'info']
    severity_weights = [0.15, 0.45, 0.40]
    
    records = []
    for i in range(num_records):
        opened = base_date + timedelta(
            days=random.randint(0, 60),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        duration_minutes = random.randint(5, 480)
        closed = opened + timedelta(minutes=duration_minutes) if random.random() > 0.1 else None
        
        record = {
            'incident_id': i + 100000,
            'account_id': 12345,
            'policy_name': random.choice(policies),
            'condition_name': random.choice(conditions),
            'entity_name': random.choice(entities),
            'entity_type': 'APPLICATION',
            'severity': random.choices(severities, weights=severity_weights)[0],
            'opened_at': opened.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'closed_at': closed.strftime('%Y-%m-%dT%H:%M:%SZ') if closed else None,
            'duration': duration_minutes * 60 if closed else None,
            'violation_url': f'https://alerts.newrelic.com/accounts/12345/incidents/{i + 100000}',
            'runbook_url': f'https://wiki.company.com/runbooks/{random.choice(conditions).lower().replace(" ", "-")}',
            'nrql_query': "SELECT average(duration) FROM Transaction WHERE appName = 'MyApp'"
        }
        records.append(record)
    
    return pd.DataFrame(records)


def generate_moogsoft_alerts(num_records: int = 500) -> pd.DataFrame:
    """Generate sample Moogsoft alert data."""
    
    base_date = datetime(2025, 1, 1)
    
    sources = ['nagios', 'prometheus', 'datadog', 'splunk', 'cloudwatch', 'custom']
    classes = ['Server', 'Network', 'Application', 'Database', 'Storage', 'Cloud']
    managers = ['Infrastructure', 'Application', 'Security', 'Business']
    
    severities = [0, 1, 2, 3, 4, 5]  # 0=clear, 5=critical
    severity_weights = [0.1, 0.15, 0.25, 0.25, 0.15, 0.1]
    
    records = []
    for i in range(num_records):
        first_event = base_date + timedelta(
            days=random.randint(0, 60),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        event_count = random.randint(1, 50)
        last_event = first_event + timedelta(minutes=random.randint(1, 120))
        
        record = {
            'alert_id': f'ALT-{i + 1:06d}',
            'moog_id': i + 1,
            'situation_id': random.randint(1, 100) if random.random() > 0.7 else None,
            'sig_id': f'SIG-{random.randint(1, 500):05d}',
            'description': f'Alert from {random.choice(sources)} - {random.choice(classes)} issue',
            'source': random.choice(sources),
            'class': random.choice(classes),
            'manager': random.choice(managers),
            'severity': random.choices(severities, weights=severity_weights)[0],
            'first_event_time': first_event.strftime('%Y-%m-%d %H:%M:%S'),
            'last_event_time': last_event.strftime('%Y-%m-%d %H:%M:%S'),
            'event_count': event_count,
            'dedup_key': f'{random.choice(sources)}:{random.choice(classes)}:{random.randint(1, 100)}',
            'agent_location': random.choice(['us-east-1', 'us-west-2', 'eu-west-1', 'ap-south-1']),
            'custom_info': '{"service": "api", "environment": "production"}'
        }
        records.append(record)
    
    return pd.DataFrame(records)


def main():
    """Generate all sample data files."""
    
    # Create sample_data directory
    os.makedirs('sample_data', exist_ok=True)
    
    print("Generating ServiceNow incidents...")
    sn_df = generate_servicenow_incidents(500)
    sn_df.to_csv('sample_data/servicenow_incidents.csv', index=False)
    print(f"  Created: sample_data/servicenow_incidents.csv ({len(sn_df)} records)")
    
    print("Generating NewRelic alerts...")
    nr_df = generate_newrelic_alerts(500)
    nr_df.to_csv('sample_data/newrelic_alerts.csv', index=False)
    print(f"  Created: sample_data/newrelic_alerts.csv ({len(nr_df)} records)")
    
    print("Generating Moogsoft alerts...")
    ms_df = generate_moogsoft_alerts(500)
    ms_df.to_csv('sample_data/moogsoft_alerts.csv', index=False)
    print(f"  Created: sample_data/moogsoft_alerts.csv ({len(ms_df)} records)")
    
    # Also create Excel version of ServiceNow data
    print("Creating Excel version...")
    sn_df.to_excel('sample_data/servicenow_incidents.xlsx', index=False)
    print(f"  Created: sample_data/servicenow_incidents.xlsx")
    
    print("\nDone! Sample data files created in sample_data/ directory.")


if __name__ == '__main__':
    main()

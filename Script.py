import json
import psycopg2

def get_value_or_default(interface, key, default=None):
    return interface.get(key, default)

def insert_interface_to_db(interface_type, interface_data):
    insert_script = '''
        INSERT INTO interfaces (connection, name, description, config, type, infra_type, port_channel_id, max_frame_size)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    insert_values = (None, interface_type + str(interface_data['name']),
                     get_value_or_default(interface_data, 'description', "description doesn't exist"),
                     json.dumps(interface_data), None, None,
                     get_value_or_default(interface_data, 'Cisco-IOS-XE-ethernet:channel-group', {}).get('number', None),
                     get_value_or_default(interface_data, 'mtu', None))

    cursor.execute(insert_script, insert_values)

# Read database credentials from a JSON file
with open('Database_credentials.json', 'r') as db_creds_file:
    db_creds = json.load(db_creds_file)

hostname = db_creds["hostname"]
database = db_creds["database"]
username = db_creds["username"]
pwd = db_creds["pwd"]
port_id = db_creds["port_id"]

try:
    # Establish database connection
    connect = psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=pwd,
        port=port_id
    )
    cursor = connect.cursor()

    # Create the table if it doesn't exist
    create_script = '''
        CREATE TABLE IF NOT EXISTS interfaces(
            id SERIAL PRIMARY KEY,
            connection INTEGER,
            name VARCHAR(255) NOT NULL,
            description VARCHAR(255),
            config json,
            type VARCHAR(50),
            infra_type VARCHAR(50),
            port_channel_id INTEGER,
            max_frame_size INTEGER
        )
    '''
    cursor.execute(create_script)

    jsonfile = open('configClear_v2.json', 'r')
    mydata = jsonfile.read()
    object = json.loads(mydata)
    uniconfig = object['frinx-uniconfig-topology:configuration']
    Cisco_ios_xe = uniconfig['Cisco-IOS-XE-native:native']
    interfaces = Cisco_ios_xe['interface']

    # Insert data for Port-channel interfaces
    Port_channel = interfaces.get('Port-channel', [])
    for interface in Port_channel:
        insert_interface_to_db("Port-channel", interface)

    # Insert data for TenGigabitEthernet interfaces
    TenGigabitEthernet = interfaces.get('TenGigabitEthernet', [])
    for interface in TenGigabitEthernet:
        insert_interface_to_db("TenGigabitEthernet", interface)

    # Insert data for GigabitEthernet interfaces
    GigabitEthernet = interfaces.get('GigabitEthernet', [])
    for interface in GigabitEthernet:
        insert_interface_to_db("GigabitEthernet", interface)

    connect.commit()
    print("Data has been inserted successfully!")

except Exception as error:
    print(error)
finally:
    if cursor is not None:
        cursor.close()
    if connect is not None:
        connect.close()

import boto3
import requests
from flask import Flask, render_template, jsonify

app = Flask(__name__)
ssm = boto3.client('ssm', region_name='ap-south-1')

def get_metadata(path):
    try:
        # 2-second timeout to prevent hang
        # The IP is a link-local address,specifically for metadata. It is unroutable
        r = requests.get(f"http://169.254.169.254/latest/meta-data/{path}", timeout=2)
        return r.text
    except:
        return "local-dev"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/about')
def about():
    return render_template('about.html')

# New Chaos Tab
@app.route('/chaos')
def chaos():
    instance_id = get_metadata("instance-id")
    az = get_metadata("placement/availability-zone")
    return render_template('chaos.html', instance_id=instance_id, az=az)

@app.route('/inject-fault/<fault_type>')
def inject_fault(fault_type):
    instance_id = get_metadata("instance-id")
    
    commands = {
        "cpu": "stress-ng --cpu 4 --timeout 60s",
        "app": "sudo systemctl stop testWebsite",
        "nginx": "sudo systemctl stop nginx"
    }

    if fault_type in commands:
        try:
            ssm.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={'commands': [commands[fault_type]]}
            )
            return jsonify({"message": f"Fault {fault_type} triggered on {instance_id}"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid fault type"}), 400

@app.route('/health')
def health():
    return {"status": "healthy", "version": "v1.1.0"}, 200

@app.route('/simulate-error')
def error(): 
    return "500 Internal Server Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)
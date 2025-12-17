from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    help = 'Test access to Google Sheet CSV export'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sheet-id',
            type=str,
            default='1fYUdK_cprGPj8UEoZVI38DiqI7P4G_loOXf8Xg62TWc',
            help='Google Sheet ID'
        )

    def handle(self, *args, **options):
        sheet_id = options['sheet_id']
        sheet_name = 'Sheet1'
        
        # Construct the CSV export URL
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
        
        self.stdout.write(self.style.SUCCESS(f'Testing access to Google Sheet: {sheet_id}'))
        self.stdout.write(self.style.SUCCESS(f'CSV URL: {csv_url}'))
        
        try:
            # Try to fetch CSV data
            response = requests.get(csv_url)
            self.stdout.write(self.style.SUCCESS(f'Status Code: {response.status_code}'))
            
            if response.status_code == 200:
                csv_text = response.text
                lines = csv_text.split('\n')
                self.stdout.write(self.style.SUCCESS(f'Success! Found {len(lines)} lines in CSV'))
                
                if lines:
                    self.stdout.write(self.style.SUCCESS('First line (headers):'))
                    self.stdout.write(lines[0])
                    
                    if len(lines) > 1:
                        self.stdout.write(self.style.SUCCESS('Second line (first patient):'))
                        self.stdout.write(lines[1])
            else:
                self.stdout.write(self.style.ERROR(f'Failed with status: {response.status_code}'))
                self.stdout.write(self.style.ERROR(f'Response: {response.text}'))
                
                self.stdout.write(self.style.WARNING('\nTo fix this issue:'))
                self.stdout.write(self.style.WARNING('1. Open your Google Sheet'))
                self.stdout.write(self.style.WARNING('2. Go to File > Share > Publish to web'))
                self.stdout.write(self.style.WARNING('3. Under "Link" tab, select "Comma-separated values (.csv)"'))
                self.stdout.write(self.style.WARNING('4. Click "Publish"'))
                self.stdout.write(self.style.WARNING('5. Wait a few minutes and try again'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

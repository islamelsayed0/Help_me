"""
Management command to backup the database.

Usage:
    python manage.py backup_database
    python manage.py backup_database --output /path/to/backup.sql
    python manage.py backup_database --compress
"""

import os
import gzip
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = 'Backup the database to a SQL file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: backups/db_backup_YYYYMMDD_HHMMSS.sql)',
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup file with gzip',
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=30,
            help='Number of backup files to keep (default: 30)',
        )

    def handle(self, *args, **options):
        # Determine output path
        if options['output']:
            output_path = Path(options['output'])
        else:
            # Create backups directory if it doesn't exist
            backups_dir = Path(settings.BASE_DIR) / 'backups'
            backups_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'db_backup_{timestamp}.sql'
            output_path = backups_dir / filename
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get database configuration
        db_config = connection.settings_dict
        
        self.stdout.write(f'Backing up database: {db_config["NAME"]}')
        
        # Determine database type
        engine = db_config['ENGINE']
        
        if 'postgresql' in engine or 'postgis' in engine:
            self.backup_postgresql(db_config, output_path, options['compress'])
        elif 'sqlite' in engine:
            self.backup_sqlite(db_config, output_path, options['compress'])
        else:
            self.stderr.write(
                self.style.ERROR(f'Unsupported database engine: {engine}')
            )
            return
        
        # Clean up old backups
        if not options['output']:  # Only cleanup if using default location
            self.cleanup_old_backups(backups_dir, options['keep'])
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Backup completed: {output_path}')
        )

    def backup_postgresql(self, db_config, output_path, compress):
        """Backup PostgreSQL database using pg_dump."""
        import subprocess
        
        # Build pg_dump command
        cmd = ['pg_dump']
        
        # Add connection parameters
        if db_config.get('HOST'):
            cmd.extend(['-h', db_config['HOST']])
        if db_config.get('PORT'):
            cmd.extend(['-p', str(db_config['PORT'])])
        if db_config.get('USER'):
            cmd.extend(['-U', db_config['USER']])
        if db_config.get('NAME'):
            cmd.extend(['-d', db_config['NAME']])
        
        # Add options
        cmd.extend(['--no-owner', '--no-acl', '--clean'])
        
        # Execute pg_dump
        try:
            env = os.environ.copy()
            if db_config.get('PASSWORD'):
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            with open(output_path, 'wb') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env
                )
                _, stderr = process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f'pg_dump failed: {stderr.decode()}')
            
            # Compress if requested
            if compress:
                self.compress_file(output_path)
                
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(
                    'pg_dump not found. Please install PostgreSQL client tools.'
                )
            )
            raise
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Backup failed: {e}'))
            raise

    def backup_sqlite(self, db_config, output_path, compress):
        """Backup SQLite database by copying the file."""
        import shutil
        
        db_path = Path(db_config['NAME'])
        
        if not db_path.exists():
            raise FileNotFoundError(f'Database file not found: {db_path}')
        
        # Copy SQLite database file
        shutil.copy2(db_path, output_path)
        
        # Compress if requested
        if compress:
            self.compress_file(output_path)

    def compress_file(self, file_path):
        """Compress a file using gzip."""
        self.stdout.write('Compressing backup...')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(f'{file_path}.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remove original file
        file_path.unlink()
        
        self.stdout.write(f'✓ Compressed: {file_path}.gz')

    def cleanup_old_backups(self, backups_dir, keep_count):
        """Remove old backup files, keeping only the most recent ones."""
        # Get all backup files
        backup_files = sorted(
            backups_dir.glob('db_backup_*.sql*'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Remove old backups
        if len(backup_files) > keep_count:
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                self.stdout.write(f'Removed old backup: {old_backup.name}')

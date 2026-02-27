"""
Database migration script
"""
from config import Config
from models.schema import Database

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Zendesk Ticket Analysis System                      ║
    ║         Database Migration                                   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        # Validate configuration
        Config.validate()

        # Initialize database
        print(f"\n📊 Connecting to database...")
        print(f"   URL: {Config.DATABASE_URL.split('@')[-1]}")  # Hide credentials

        database = Database(Config.DATABASE_URL)

        # Create tables
        print(f"\n🏗️  Creating database tables...")
        database.create_tables()

        print(f"\n✅ Migration completed successfully!")
        print(f"\nTables created:")
        print(f"   - tickets")
        print(f"   - comments")
        print(f"   - ticket_metrics")
        print(f"   - ticket_audits")
        print(f"   - ai_analysis")
        print(f"   - custom_field_mappings")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()

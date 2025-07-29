#!/usr/bin/env python3
"""
Coffee Data Processing Script with Selective Processing

Features:
- Hash-based change detection for efficient selective processing
- Version-aware processing with metadata tracking
- Field validation and consistency checking
- Comprehensive processing statistics and debugging

Usage:
    python process_coffee_data.py [input_file] [output_file] [options]
    
Examples:
    python process_coffee_data.py                                    # Process cups_of_coffee.csv in-place
    python process_coffee_data.py data/my_data.csv                   # Process specific file in-place
    python process_coffee_data.py input.csv output.csv               # Process to different output file
    python process_coffee_data.py --force-full                       # Process all entries (ignore hashes)
    python process_coffee_data.py --stats --debug-hash               # Show detailed stats
    python process_coffee_data.py --version 1.3.0                    # Use specific version
    python process_coffee_data.py --dry-run                          # Preview changes
    python process_coffee_data.py --config config.json               # Custom configuration

Selective Processing:
- Only processes entries that have changed, are missing calculations, or have version mismatches
- Adds metadata columns: raw_data_hash, calculation_version, last_processed_timestamp
- Provides >85% computational savings for typical update scenarios
- Works regardless of how CSV files are edited (direct editing, programmatic updates, etc.)
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import json
from src.processing.process_entry_data import CoffeeDataProcessor, SelectiveDataProcessor

def main():
    parser = argparse.ArgumentParser(description='Process coffee brewing data with selective processing')
    parser.add_argument('input_file', nargs='?', default='data/cups_of_coffee.csv',
                       help='Input CSV file (default: data/cups_of_coffee.csv)')
    parser.add_argument('output_file', nargs='?', 
                       help='Output CSV file (default: same as input file)')
    parser.add_argument('--config', help='Config file for custom processing parameters')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without saving')
    parser.add_argument('--selective', action='store_true', default=True, 
                       help='Use selective processing (hash-based change detection) - default: True')
    parser.add_argument('--force-full', action='store_true', 
                       help='Force full processing (ignore hashes and process all entries)')
    parser.add_argument('--version', default='1.2.0', 
                       help='Target calculation version (default: 1.2.0)')
    parser.add_argument('--stats', action='store_true', 
                       help='Show detailed processing statistics')
    parser.add_argument('--debug-hash', action='store_true', 
                       help='Show hash debugging information')
    
    args = parser.parse_args()
    
    # Check if input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    try:
        # Load configuration if provided
        config = {}
        if args.config:
            try:
                with open(args.config, 'r') as f:
                    config = json.load(f)
                print(f"Loaded configuration from {args.config}")
            except Exception as e:
                print(f"Warning: Could not load config file {args.config}: {e}")
        
        # Load data
        print(f"Loading data from {args.input_file}...")
        df = pd.read_csv(args.input_file)
        print(f"Loaded {len(df)} rows")
        
        # Set output file to input file if not specified
        output_file = args.output_file if args.output_file else args.input_file
        
        # Determine processing mode
        use_selective = args.selective and not args.force_full
        
        if use_selective:
            print(f"Using selective processing (version {args.version})...")
            processor = SelectiveDataProcessor(config=config, target_version=args.version)
            processed_df, stats = processor.process_selective_update(df)
            
            # Display processing statistics
            print(f"\n📊 Processing Statistics:")
            print(f"  • Processed: {stats['entries_processed']}/{stats['total_entries']} entries")
            print(f"  • Efficiency: {stats['efficiency_ratio']:.1%} computational savings")
            print(f"  • Time: {stats['processing_time_seconds']:.3f}s")
            
            # Show which brew IDs were processed
            if 'processed_brew_ids' in stats and stats['processed_brew_ids']:
                brew_ids = sorted(stats['processed_brew_ids'])
                print(f"  • Processed brew IDs: {brew_ids}")
            
            if stats['trigger_breakdown']:
                print(f"  • Triggers: {dict(stats['trigger_breakdown'])}")
            
            if args.stats:
                print(f"\n📈 Detailed Statistics:")
                print(f"  • Hash mismatches: {stats['hash_mismatches_count']}")
                print(f"  • Validation failures: {stats['validation_failures_count']}")
                print(f"  • Processing decisions: {stats['processing_decisions_count']}")
            
            if args.debug_hash and len(df) > 0:
                debug_info = processor.get_hash_debugging_info(df)
                print(f"\n🔍 Hash Debug Info:")
                print(f"  • Raw fields: {debug_info['raw_fields_used']}")
                print(f"  • Algorithm: {debug_info['hash_algorithm']}")
                if debug_info['sample_hash_calculation']:
                    print(f"  • Sample hash: {debug_info['sample_hash_calculation']['calculated_hash'][:16]}...")
        else:
            print("Using full processing (processing all entries)...")
            processor = CoffeeDataProcessor(config)
            processed_df = processor.process_dataframe(df)
        
        if args.dry_run:
            print("\n🧪 DRY RUN - Would save processed data with:")
            print(f"  • Rows: {len(processed_df)}")
            new_columns = [col for col in processed_df.columns if col not in df.columns]
            print(f"  • New columns: {new_columns}")
            if use_selective:
                metadata_cols = [col for col in new_columns if col in SelectiveDataProcessor.METADATA_COLUMNS]
                if metadata_cols:
                    print(f"  • Metadata columns: {metadata_cols}")
        else:
            # Save processed data
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            processed_df.to_csv(output_file, index=False)
            
            mode_desc = "selective" if use_selective else "full"
            same_file_note = " (updated in-place)" if output_file == args.input_file else ""
            print(f"✓ Processed data saved to {output_file} ({mode_desc} processing){same_file_note}")
        
    except Exception as e:
        print(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
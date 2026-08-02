import polars as pl
from typing import Dict, List, Any, Optional


class Differ:
    """
    Compares source and target data to find differences.
    
    Uses Polars for efficient join operations and column-wise comparison.
    Handles both existing column updates and new column addition.
    """
    
    def __init__(self, session_data: Dict[str, Any]):
        """Initialize the differ with session configuration.
        
        Args:
            session_data: Dictionary containing:
                - source_path, target_path: File paths
                - source_sku_col, target_sku_col: SKU column names
                - column_mapping: Dict with 'updates' and 'new_columns'
                - output_path: Output file path
        """
        self.source_path = session_data['source_path']
        self.target_path = session_data['target_path']
        self.source_sku_col = session_data['source_sku_col']
        self.target_sku_col = session_data['target_sku_col']
        self.column_mapping = session_data['column_mapping']
        self.output_path = session_data.get('output_path', '')
        
        self.source_df = None
        self.target_df = None
        self.updates = []
        self.additions = None
        self.new_columns_data = {}
        self.warnings = []
    
    def compare(self) -> Dict[str, Any]:
        """Perform the full comparison between source and target.
        
        Returns:
            Dictionary with comparison results:
                - updates: List of cell update dicts
                - additions: DataFrame of rows to add
                - new_columns_data: Dict of new column data by row
                - warnings: List of warning dicts
                - source_rows, target_rows: Row counts
                - columns_matched: Number of matched columns
                - new_columns_count: Number of new columns
                - new_skus: Number of new SKUs to add
        """
        # Read source and target files
        self._read_source()
        self._read_target()
        
        # Clean and deduplicate source data
        self._clean_source()
        self._deduplicate_source()
        
        # Perform join and comparison operations
        self._perform_comparison()
        
        return {
            'updates': self.updates,
            'additions': self.additions,
            'new_columns_data': self.new_columns_data,
            'warnings': self.warnings,
            'source_rows': len(self.source_df),
            'target_rows': (
                len(self.target_df) if self.target_df is not None else 0
            ),
            'columns_matched': len(
                self.column_mapping.get('updates', {})
            ),
            'new_columns_count': len(
                self.column_mapping.get('new_columns', {})
            ),
            'new_skus': (
                len(self.additions) if self.additions is not None else 0
            )
        }
    
    def _read_source(self):
        """Read source file into DataFrame."""
        if self.source_path.endswith('.csv'):
            encoding = self._detect_encoding(self.source_path)
            self.source_df = pl.read_csv(
                self.source_path,
                has_header=True,
                encoding=encoding,
                truncate_ragged_lines=True
            )
        else:
            self.source_df = pl.read_excel(
                self.source_path,
                engine='calamine'
            )
    
    def _read_target(self):
        """Read target file efficiently - only needed columns.
        Supports both CSV and Excel formats with encoding detection."""
        update_columns = list(self.column_mapping.get('updates', {}).values())
        
        if self.target_sku_col not in update_columns:
            update_columns.append(self.target_sku_col)
        
        if self.target_path.endswith('.csv'):
            encoding = self._detect_encoding(self.target_path)
            self.target_df = pl.read_csv(
                self.target_path,
                has_header=True,
                encoding=encoding,
                columns=update_columns,
                truncate_ragged_lines=True
            )
        else:
            self.target_df = pl.read_excel(
                self.target_path,
                engine='calamine',
                columns=update_columns
            )
    
    @staticmethod
    def _detect_encoding(file_path):
        """Detect file encoding for CSV files."""
        import chardet
        with open(file_path, 'rb') as f:
            raw = f.read(50000)
            result = chardet.detect(raw)
            return result['encoding'] or 'utf-8'
    
    def _clean_source(self):
        """Clean source data - remove checkmarks and empty values."""
        all_source_cols = (
            list(self.column_mapping.get('updates', {}).keys()) +
            list(self.column_mapping.get('new_columns', {}).keys())
        )
        
        cleaning_exprs = []
        for source_col in all_source_cols:
            if source_col in self.source_df.columns:
                cleaning_exprs.append(
                    pl.when(
                        pl.col(source_col)
                        .cast(pl.Utf8)
                        .str.strip_chars()
                        .is_in([
                            '✔', '✓', '√', '✅', '☑',
                            '', ' ', 'N/A', 'n/a'
                        ])
                    )
                    .then(None)
                    .otherwise(pl.col(source_col))
                    .alias(source_col)
                )
        
        if cleaning_exprs:
            self.source_df = self.source_df.with_columns(cleaning_exprs)
    
    def _deduplicate_source(self):
        """Deduplicate source data by SKU, keeping first occurrence."""
        sku_col = self.source_sku_col
        
        # Find duplicates
        duplicates = (
            self.source_df
            .group_by(sku_col)
            .len()
            .filter(pl.col('len') > 1)
        )
        
        if len(duplicates) > 0:
            dup_skus = duplicates[sku_col].to_list()
            self.warnings.append({
                'type': 'duplicate_sku',
                'message': (
                    f'Found {len(dup_skus)} duplicate SKUs in source file. '
                    f'Keeping first occurrence.'
                ),
                'skus': dup_skus,
                'count': len(dup_skus)
            })
            
            # Keep only first occurrence of each SKU
            self.source_df = self.source_df.unique(
                subset=[sku_col],
                keep='first'
            )
    
    def _perform_comparison(self):
        """Execute join operations and column comparisons."""
        # Validate SKU columns exist
        if self.source_sku_col not in self.source_df.columns:
            raise ValueError(
                f"Source SKU column '{self.source_sku_col}' not found"
            )
        if self.target_sku_col not in self.target_df.columns:
            raise ValueError(
                f"Target SKU column '{self.target_sku_col}' not found"
            )
        
        # Rename SKU columns to common name for joining
        source_renamed = self.source_df.rename(
            {self.source_sku_col: '__SKU__'}
        )
        target_renamed = self.target_df.rename(
            {self.target_sku_col: '__SKU__'}
        )
        
        # Find common SKUs (inner join) and new SKUs (anti join)
        common_skus = (
            source_renamed
            .select('__SKU__')
            .join(
                target_renamed.select('__SKU__'),
                on='__SKU__',
                how='inner'
            )
        )
        
        new_skus = (
            source_renamed
            .select('__SKU__')
            .join(
                target_renamed.select('__SKU__'),
                on='__SKU__',
                how='anti'
            )
        )
        
        # Compare existing columns for common SKUs
        self._compare_common_rows(
            source_renamed, target_renamed, common_skus
        )
        
        # Process new columns to be added
        self._process_new_columns(source_renamed, target_renamed)
        
        # Prepare new rows for SKUs only in source
        self._prepare_additions(source_renamed, new_skus)
    
    def _compare_common_rows(
        self,
        source_df: pl.DataFrame,
        target_df: pl.DataFrame,
        common_skus: pl.DataFrame
    ):
        """Compare values for common SKUs column by column."""
        update_mapping = self.column_mapping.get('updates', {})
        if not update_mapping:
            self.updates = []
            return
        
        # Filter to common SKUs only
        source_common = source_df.join(common_skus, on='__SKU__', how='inner')
        target_common = target_df.join(common_skus, on='__SKU__', how='inner')
        
        source_cols = list(update_mapping.keys())
        target_cols = list(update_mapping.values())
        
        target_rename = {col: f'{col}_target' for col in target_cols}
        
        src_selected = source_common.select(
            ['__SKU__'] + [c for c in source_cols if c in source_common.columns]
        )
        tgt_selected = target_common.select(
            ['__SKU__'] + [c for c in target_cols if c in target_common.columns]
        ).rename(target_rename)
        
        combined = src_selected.join(tgt_selected, on='__SKU__', how='inner')
        
        updates = []
        for src_col, tgt_col in update_mapping.items():
            tgt_renamed = f'{tgt_col}_target'
            if src_col not in combined.columns or tgt_renamed not in combined.columns:
                continue
            
            diffs = combined.filter(
                pl.col(src_col).is_not_null() &
                (
                    pl.col(tgt_renamed).is_null() |
                    (pl.col(src_col).cast(pl.Utf8) != pl.col(tgt_renamed).cast(pl.Utf8))
                )
            )
            
            if diffs.is_empty():
                continue
            
            col_updates = diffs.select(
                pl.col('__SKU__').alias('sku'),
                pl.lit(tgt_col).alias('column'),
                pl.lit(src_col).alias('source_column'),
                pl.col(tgt_renamed).alias('old_value'),
                pl.col(src_col).alias('new_value'),
            ).to_dicts()
            
            updates.extend(col_updates)
        
        self.updates = updates
    
    def _process_new_columns(
        self,
        source_df: pl.DataFrame,
        target_df: pl.DataFrame
    ):
        """Process new columns to be added to target file."""
        new_columns_mapping = self.column_mapping.get('new_columns', {})
        if not new_columns_mapping:
            return
        
        # Get target SKUs with row indices for alignment
        target_skus = target_df.select('__SKU__').with_row_index(
            name='row_idx'
        )
        
        existing_src_cols = [
            src for src in new_columns_mapping.keys()
            if src in source_df.columns
        ]
        if not existing_src_cols:
            return
        
        rename_map = {
            src: new_columns_mapping[src]
            for src in existing_src_cols
        }
        src_data = source_df.select(
            ['__SKU__'] + existing_src_cols
        ).rename(rename_map)
        
        aligned = target_skus.join(src_data, on='__SKU__', how='left')
        
        for new_col in rename_map.values():
            self.new_columns_data[new_col] = aligned.select(
                pl.col('row_idx'),
                pl.col(new_col)
            )
    
    def _prepare_additions(
        self,
        source_df: pl.DataFrame,
        new_skus: pl.DataFrame
    ):
        """Prepare new rows to be added for SKUs only in source.
        
        Args:
            source_df: Source DataFrame with renamed SKU column.
            new_skus: DataFrame of SKUs present only in source.
        """
        # Get source rows for new SKUs
        additions = source_df.join(new_skus, on='__SKU__', how='inner')
        
        # Combine all column mappings
        all_mappings = {}
        all_mappings.update(self.column_mapping.get('updates', {}))
        all_mappings.update(self.column_mapping.get('new_columns', {}))
        
        # Rename source columns to match target column names
        rename_map = {'__SKU__': self.target_sku_col}
        for source_col, target_col in all_mappings.items():
            if source_col in additions.columns:
                rename_map[source_col] = target_col
        
        self.additions = additions.rename(rename_map)
        
        # Keep only columns that exist in target (or will be added)
        mapped_target_cols = (
            list(all_mappings.values()) + [self.target_sku_col]
        )
        cols_to_keep = [
            c for c in self.additions.columns if c in mapped_target_cols
        ]
        self.additions = self.additions.select(cols_to_keep)
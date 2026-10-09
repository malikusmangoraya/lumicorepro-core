import React, { useState, useMemo } from 'react';
import { cn } from '../../utils';
import { ChevronUp, ChevronDown, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import Button from './Button';
import Input from '../forms/Input';
import Badge from './Badge';

const DataTable = React.forwardRef(
  (
    {
      columns = [],
      data = [],
      searchable = true,
      sortable = true,
      pagination = true,
      pageSize = 10,
      pageSizeOptions = [10, 25, 50, 100],
      emptyMessage = 'No data available',
      loading = false,
      className = '',
      onRowClick,
      rowKey = 'id',
      striped = true,
      hoverable = true,
      ...props
    },
    ref
  ) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [currentPage, setCurrentPage] = useState(1);
    const [selectedPageSize, setSelectedPageSize] = useState(pageSize);

    const filteredData = useMemo(() => {
      let result = [...data];
      
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        result = result.filter(row =>
          columns.some(col => {
            const value = row[col.key];
            return value?.toString().toLowerCase().includes(term);
          })
        );
      }
      
      if (sortConfig.key && sortable) {
        result.sort((a, b) => {
          const aVal = a[sortConfig.key];
          const bVal = b[sortConfig.key];
          if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
          if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
          return 0;
        });
      }
      
      return result;
    }, [data, searchTerm, sortConfig, columns, sortable]);

    const paginatedData = useMemo(() => {
      if (!pagination) return filteredData;
      const start = (currentPage - 1) * selectedPageSize;
      return filteredData.slice(start, start + selectedPageSize);
    }, [filteredData, pagination, currentPage, selectedPageSize]);

    const totalPages = Math.ceil(filteredData.length / selectedPageSize);

    const handleSort = (key) => {
      if (!sortable) return;
      setSortConfig(prev => ({
        key,
        direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
      }));
    };

    const handlePageChange = (page) => {
      setCurrentPage(Math.max(1, Math.min(page, totalPages)));
    };

    const handlePageSizeChange = (size) => {
      setSelectedPageSize(size);
      setCurrentPage(1);
    };

    const getSortIcon = (key) => {
      if (sortConfig.key !== key) return null;
      return sortConfig.direction === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
    };

    if (loading) {
      return (
        <div className={cn('space-y-4', className)}>
          <div className="animate-pulse space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      );
    }

    return (
      <div className={cn('space-y-4', className)} {...props}>
        {searchable && (
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <Input
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-10"
              inputClassName="pr-10"
            />
          </div>
        )}
        
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full" role="grid">
            <thead className="bg-muted/50">
              <tr>
                {columns.map((column) => (
                  <th
                    key={column.key}
                    scope="col"
                    className={cn(
                      'px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider',
                      column.align === 'center' && 'text-center',
                      column.align === 'right' && 'text-right',
                      sortable && column.sortable !== false && 'cursor-pointer select-none hover:bg-muted',
                      column.width && `w-[${column.width}]`
                    )}
                    onClick={() => handleSort(column.key)}
                    style={{ width: column.width }}
                  >
                    <div className="flex items-center gap-1.5 justify-start">
                      {column.label}
                      {sortable && column.sortable !== false && getSortIcon(column.key)}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-12 text-center text-muted-foreground">
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                paginatedData.map((row, rowIndex) => (
                  <tr
                    key={row[rowKey] || rowIndex}
                    className={cn(
                      'transition-colors',
                      striped && rowIndex % 2 === 1 && 'bg-muted/30',
                      hoverable && 'hover:bg-muted/50',
                      onRowClick && 'cursor-pointer'
                    )}
                    onClick={() => onRowClick?.(row)}
                  >
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={cn(
                          'px-4 py-3 text-sm',
                          column.align === 'center' && 'text-center',
                          column.align === 'right' && 'text-right'
                        )}
                      >
                        {column.render
                          ? column.render(row[column.key], row)
                          : row[column.key]}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {pagination && totalPages > 1 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-2">
            <div className="text-sm text-muted-foreground">
              Showing <span className="font-medium">{(currentPage - 1) * selectedPageSize + 1}</span> to{' '}
              <span className="font-medium">{Math.min(currentPage * selectedPageSize, filteredData.length)}</span>{' '}
              of <span className="font-medium">{filteredData.length}</span> results
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedPageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                className="px-3 py-1.5 text-sm border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Rows per page"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size} per page
                  </option>
                ))}
              </select>
              <Button
                variant="ghost"
                size="sm"
                icon={ChevronLeft}
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                aria-label="Previous page"
              />
              <span className="text-sm font-medium px-2">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                rightIcon={ChevronRight}
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                aria-label="Next page"
              />
            </div>
          </div>
        )}
      </div>
    );
  }
);

DataTable.displayName = 'DataTable';

export default DataTable;
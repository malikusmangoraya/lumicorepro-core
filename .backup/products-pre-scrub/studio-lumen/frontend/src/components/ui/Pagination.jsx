import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const Pagination = ({
  currentPage = 1,
  totalPages = 1,
  totalItems,
  pageSize,
  onPageChange,
  onChange,
  siblingCount = 1,
  showPageNumbers = true,
  showFirstLast = true,
  animate = 'none',
  className = '',
}) => {
  const notify = onPageChange || onChange;

  const generatePageNumbers = () => {
    const pages = [];
    const totalPageNumbers = siblingCount * 2 + 5;

    if (totalPages <= totalPageNumbers) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      const leftSiblingIndex = Math.max(currentPage - siblingCount, 1);
      const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages);
      const shouldShowLeftDots = leftSiblingIndex > 2;
      const shouldShowRightDots = rightSiblingIndex < totalPages - 2;

      if (!shouldShowLeftDots && shouldShowRightDots) {
        for (let i = 1; i <= 3 + siblingCount * 2; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (shouldShowLeftDots && !shouldShowRightDots) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - (3 + siblingCount * 2 - 1); i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = leftSiblingIndex; i <= rightSiblingIndex; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    return pages;
  };

  const pageNumbers = generatePageNumbers();
  const goTo = (page) => {
    if (page < 1 || page > totalPages || page === currentPage) return;
    notify?.(page);
  };

  const buttonBase =
    'inline-flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 disabled:pointer-events-none active:scale-95';

  return (
    <nav
      className={cn(
        'flex flex-col sm:flex-row items-center justify-between gap-4',
        getAnimationClass(animate),
        className
      )}
      aria-label="Pagination"
    >
      <p className="text-sm text-muted-foreground">
        Page <span className="font-medium text-foreground">{currentPage}</span> of{' '}
        <span className="font-medium text-foreground">{totalPages}</span>
        {totalItems !== undefined && (
          <>
            {' '}
            · <span className="font-medium text-foreground">{totalItems}</span> items
          </>
        )}
        {pageSize !== undefined && <span className="sr-only">, {pageSize} per page</span>}
      </p>

      <div className="flex items-center gap-1">
        {showFirstLast && (
          <button
            type="button"
            className={cn(buttonBase, 'text-foreground hover:bg-muted')}
            onClick={() => goTo(1)}
            disabled={currentPage === 1}
            aria-label="Go to first page"
          >
            <span aria-hidden="true">«</span>
          </button>
        )}

        <button
          type="button"
          className={cn(buttonBase, 'text-foreground hover:bg-muted')}
          onClick={() => goTo(currentPage - 1)}
          disabled={currentPage === 1}
          aria-label="Go to previous page"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </button>

        {showPageNumbers &&
          pageNumbers.map((page, index) =>
            page === '...' ? (
              <span key={`dots-${index}`} className="px-2 text-muted-foreground" aria-hidden="true">
                …
              </span>
            ) : (
              <button
                key={page}
                type="button"
                className={cn(
                  buttonBase,
                  currentPage === page
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground hover:bg-muted'
                )}
                onClick={() => goTo(page)}
                aria-current={currentPage === page ? 'page' : undefined}
                aria-label={`Go to page ${page}`}
              >
                {page}
              </button>
            )
          )}

        <button
          type="button"
          className={cn(buttonBase, 'text-foreground hover:bg-muted')}
          onClick={() => goTo(currentPage + 1)}
          disabled={currentPage === totalPages}
          aria-label="Go to next page"
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>

        {showFirstLast && (
          <button
            type="button"
            className={cn(buttonBase, 'text-foreground hover:bg-muted')}
            onClick={() => goTo(totalPages)}
            disabled={currentPage === totalPages}
            aria-label="Go to last page"
          >
            <span aria-hidden="true">»</span>
          </button>
        )}
      </div>
    </nav>
  );
};

export default Pagination;

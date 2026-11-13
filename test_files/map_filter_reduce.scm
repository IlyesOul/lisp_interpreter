(begin

(define (map func ls)
    (map_helper func ls 0)
)

(define (map_helper func ls index)
    (if (>= index (length ls)) ()
        (cons (func (list-ref ls index)) (map_helper func ls (+ 1 index)))
    )
)

(define (filter func ls)
    (filter_helper func ls 0)
)

(define (filter_helper func ls index)
    (if (>= index (length ls)) ()
        (if (func (list-ref ls index)) (cons (list-ref ls index) (filter_helper func ls (+ 1 index))) (filter_helper func ls (+ 1 index)))
    )
)


(define (reduce func ls val)
    (reduce_helper func ls val 0)
)

(define (reduce_helper func ls val index)
    (if (equal? index (length ls)) val
        (reduce_helper func ls (func val (list-ref ls index)) (+ 1 index))
    )
)
)
(define err-empty-list 'err-empty-list)
			
;; Checks if list is empty
(define empty-list?
  (lambda (l)
    ;; (= l ())))
    (if (= l ()) t nil)))


;; Length function for lists
(define length 
  ;; Helper for memoization
    (let ((length-tailrec (lambda (l sum)
			    (if (empty-list? l) sum
				(length-tailrec (tail l) (+ sum 1))))))
    (lambda (l) (length-tailrec l 0))))


;; Reverse a list
(define reverse
  (let reverse-rec (lambda (l acc)
      (if (empty-list? l) acc
          (reverse-rec (tail l) (cons (head l) acc))))
   (lambda (l) (reverse-rec l ())))) 
     

(define accumulate
    (lambda (foos x)
      (cond ((empty-list? foos) x)
	    (t (accumulate (tail foos) ((head foos) x))))))
      
    
;; nth element of a list
(define nth
  (lambda (l n)
    (cond ((empty-list? l) 'err-empty-list)
          ((= n 0) (head l))
          (t (nth (tail l) (- n 1))))))

;; last element of a list
(define last
  (lambda (l) (nth l (- (length l) 1))))

;; Ritorna una lista dei primi n numeri di Fibonacci
(define fast-fibo-list
  (lambda (n memo)
    (if (> n (length memo))
      (fast-fibo-list n 
                (cons (+ (nth memo 0) (nth memo 1)) memo))
      memo)))

(define fast-fibo-general
  (lambda (n memo) (head (fast-fibo-list n memo))))

(define fast-fibo
  (lambda (n) (fast-fibo-general n (list 1 1))))

;; Seq from to
(define seq
  (let seq-rec
    (lambda (start end acc)
      (if (>= start end) acc
          (seq-rec (+ 1 start) end (append start acc))))
    (lambda (start end) (seq-rec start end ()))))

(define zip 
 (let zip-rec 
    (lambda (l1 l2 acc)
       (if (or (empty-list? l1) (empty-list? l2)) acc
       (let ((h1 (head l1))
	     (h2 (head l2)))
	 (zip-rec (tail l1) (tail l2) (cons (list h1 h2) acc)))))

  (lambda (l1 l2) (zip-rec l1 l2 ()))))

(define fact
    (let fact-rec
      (lambda (n temp)
	(if (< n 2) temp (fact-rec (- n 1) (* temp n))))
      (lambda (n) (fact-rec n 1))))

;;;;;;;;;;;;;;;;;;;

(define if-macro-substitute
  (lambda (E)
    (let ((condition (nth E 1))
	  (then (nth E 2))
	  (else (nth E 3)))
      (list 'cond (list condition then)
	    (list t else)))))
      
(define if-macro-checker
  (lambda (E)
    (cond ((atom? E) E)
	  ((= (head E) 'if) (if-macro-substitute E))
	  (t (map if-macro-checker E)))))

;; (macro if-macro-checker)

;;;;;;;;;;;;;;;;;;;;;;;


;; (define lookup
;;     (lambda (context symbol)

;; (define my-eval
;;   (lambda (C E)
;;     (cond ((atom? E) E) ;; sbagliato: (eval '++) dovrebbe ritornare la funzione, non "++"
;; 	  ((= (head E) 'cond)
;; 	   (let c (

(define for-macro-expander
  (lambda (E)
   (list 'map (list 'lambda (nth E 1) (nth E 5)) (nth E 3)))) 

(define for-macro-sub 
  (lambda (E)
    (if (not (is-list? E)) E
        (if (and (> (length E) 0) (= (nth E 0) 'for))
	    (for-macro-expander E)
	    (map for-macro-sub E)))))

;;;;;;;;;;;;

(define metacircular
  (lambda (macros-list)
    (let ((inp (read "Mλ. "))
	  (_ (print (eval (accumulate macros-list inp))))) 
      (cond ((= inp "quit") '())
	    (t (metacircular macros-list))))))

;; (metacircular (list if-macro-checker for-macro-sub))

;;;;;;;;;;;;

(define loop
  (lambda (f)
    (begin
     (f)
     (loop f))))

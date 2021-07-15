(define err-empty-list 'err-empty-list)
			
;; Checks if list is empty
(define empty-list?  
  (lambda (l) "Checks if a list is empty." (= l '())))

(define filter
    (lambda (f l) "Filter HOF"
      (fold (lambda (x acc) (if (f x) (append x acc) acc)) '() l)))

(define length 
    (lambda (l) "List length"
      (fold (lambda (_ acc) (++ acc)) 0 l)))

;; (let start (time) (begin (E) (print (- (time) start))))

;; Reverse a list
(define reverse
    (lambda (l) "Reverse a list"
      (fold (lambda (x acc) (cons x acc)) '() l)))

;; (define ex (repeat-until *2 "x" (lambda (acc) (> (length acc) 800))))

;; nth element of a list
;; (define nth
;;   (lambda (l n) "Returns nth element of a list." 
;;     (cond ((empty-list? l) 'err-empty-list)
;;           ((= n 0) (head l))
;;           (t (nth (tail l) (- n 1))))))


;; last element of a list
(define last
  (lambda (l) "Returns last element of a list."
    (nth l (- (length l) 1))))


;; Seq from to
(define seq
  (lambda (start end) "List of numbers from start to end"
    (if (> start end) '() 
	(reverse
	 (repeat-until (lambda (acc) (cons (++ (head acc)) acc))
		       (list start)
		       (lambda (acc) (= (head acc) (- end 1))))))))


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Ritorna una lista dei primi n numeri di Lucas

(define lucas-list
  (lambda (n start)
    (cond ((< n 0) '())
	  ((< n 2) (nth start n))
	  (t (fold (lambda (x acc)
	             (cons (+ (nth acc 0) (nth acc 1)) acc))
		   start
		   (seq 2 n))))))

(define lucas
   (lambda (n memo) "Generates the nth Lucas number, given a starting list."
      (head (lucas-list n memo))))


(define fibo
  (lambda (n) "Generates the nth fibonacci number."
     (lucas n '(1 1))))

;;;;;;;;;;;;;;;;;;;;;;;;;;;

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

(define accumulate
    (lambda (foos x)
      (cond ((empty-list? foos) x)
	    (t (accumulate (tail foos) ((head foos) x))))))

(define metacircular
  (lambda (macros-list)
    (let ((inp (read "Mλ. "))
	  (_ (print (eval (accumulate macros-list inp))))) 
      (cond ((= inp "quit") '())
	    (t (metacircular macros-list))))))

;; (metacircular (list if-macro-checker for-macro-sub))

;;;;;;;;;;;;

(define import
    (lambda (fpath)
      (evalS (read-file fpath))))

(define loop
  (lambda (f)
    (begin
     (f)
     (loop f))))

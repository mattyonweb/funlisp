(define cpx
    (lambda (real imag) (list real imag)))
(define real
    (lambda (cpx) (head cpx)))
(define imag
    (lambda (cpx) (last cpx)))

(define cpx-sum
    (lambda (c1 c2) "Complex sum"
      (cpx (+ (real c1) (real c2))
	   (+ (imag c1) (imag c2)))))

(define cpx-square
    (lambda (c) "Complex squaring"
      (let ((r (real c))
	    (i (imag c)))
	(cpx (- (** r 2) (** i 2))
	     (* 2 r i)))))

(define cpx-abs-square
    (lambda (c) "Complex magnitude"
      (+ (** (real c) 2)
	 (** (imag c) 2))))

(define converge? 
    (lambda (c iters) "Convergence test for complex numbers"
    (head
      (repeat-until
       (lambda (acc) (list (++ (head acc))
			   (cpx-sum (cpx-square (last acc)) c)))
       (list 0 c)
       (lambda (acc) (or (>= (head acc) iters)
			 (> (cpx-abs-square (last acc)) 4)))))))

(define seq-step
    (lambda (start end step) (reverse
      (repeat-until (lambda (acc) (cons (+ (head acc) step) acc))
		    (list start)
		    (lambda (acc) (= (head acc) end))))))

;;;;;;;;;;;;;;;;;;;;;;

(define width-pixel 256)
(define height-pixel 256)

(define maprange
    (lambda (max-pix pix)
      (- (/ (* 4 pix) max-pix) 2)))


(define nth-row
  (lambda (y)
    (let calculation
      (compose  (lambda (c) (+ (show (converge? c 10)) " "))
       (compose (lambda (x) (cpx x (maprange height-pixel y)))
		(lambda (x1) (maprange width-pixel x1))))
      (map calculation (seq 0 width-pixel)))))


(define flatten-str
    (lambda (ls)
      (fold (lambda (x acc) (+ acc x)) "" ls)))

(define \n
    "
")

;;;;;;;;;;;;;;;;;;;;;;;;;

(let start (time)
 (begin
  (write-file "out.pbm" "")
  (append-to-file "out.pbm"
		  (+ "P2" \n
		     (show width-pixel) " " (show height-pixel) \n
		     "10" \n))
  (map (lambda (x)
	 (begin
	  (print x)
	  (append-to-file "out.pbm" (+ (flatten-str (nth-row x)) \n))))
       (seq 0 height-pixel))
  (print (- (time) start))))

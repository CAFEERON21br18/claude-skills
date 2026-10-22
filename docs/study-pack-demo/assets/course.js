/* Demo course data shared by the three pages. In real use, study-pack writes this from your own notes. */
window.COURSE = {
  name: "Linear Algebra",
  examInDays: 11,
  topics: [
    {
      n: 1, name: "Linear systems and Gauss elimination",
      syllabus: [
        "System \\(A\\mathbf x=\\mathbf b\\) → augmented matrix \\([A\\,|\\,\\mathbf b]\\)",
        "Row operations: swap, scale by \\(\\alpha\\ne0\\), add a multiple of a row",
        "Echelon form: each pivot strictly right of the one above",
        "Pivot column → dependent variable; no pivot → free variable",
        "Row \\(0\\cdots0\\,|\\,c\\) with \\(c\\ne0\\) ⇒ no solution",
        "No free variable ⇒ unique; at least one ⇒ infinitely many"
      ],
      lead: "Forget the letters: work only on the augmented matrix \\([A\\,|\\,\\mathbf b]\\). Row operations never change the solutions, so you push the matrix into a staircase and simply read the answer.",
      defs: [
        ["Echelon form", "Zero rows at the bottom, and each pivot (first non-zero entry of a row) strictly to the right of the pivot above."],
        ["Reading the result", "A row \\(0\\ \\cdots\\ 0\\,|\\,c\\) with \\(c\\ne0\\) means no solution. Otherwise: no free variable gives one solution, at least one gives infinitely many."]
      ],
      trap: "With a parameter, never divide by an expression that can be zero, like \\(k-3\\). The values that kill a pivot are exactly the cases to study separately.",
      worked: {
        title: "Solve a 2 × 2 system",
        math: "\\[\\left[\\begin{array}{cc|c}1&2&5\\\\3&4&11\\end{array}\\right]\\xrightarrow{L_2-3L_1}\\left[\\begin{array}{cc|c}1&2&5\\\\0&-2&-4\\end{array}\\right]\\]",
        steps: ["Last row: \\(-2y=-4\\), so \\(y=2\\).", "First row: \\(x=5-2\\cdot2=1\\).", "Two pivots, no free variable: one solution \\((1,2)\\)."]
      },
      ex: [
        { type: "mcq", src: "Sheet 1 · Ex 3", q: "The system \\(x+y=2,\\ 2x+2y=5\\) has…", opts: ["exactly one solution", "infinitely many solutions", "no solution", "it depends on \\(x\\)"], ans: 2,
          why: "\\(L_2-2L_1\\) gives \\(0=1\\): impossible. A is the classic mistake of not checking the last row; B confuses two parallel lines with the same line; D makes no sense, a system has a fixed number of solutions." },
        { type: "mcq", src: "Sheet 1 · Ex 7", q: "After elimination a system in \\(x,y,z\\) gives \\(\\left[\\begin{array}{ccc|c}1&2&-1&3\\\\0&1&4&2\\\\0&0&0&0\\end{array}\\right]\\). How many free variables?", opts: ["0", "1", "2", "3"], ans: 1,
          why: "Pivots in the \\(x\\) and \\(y\\) columns only, so \\(z\\) is free: one free variable. A forgets that a zero row means a missing pivot; C counts the zero row as two; D counts all unknowns." },
        { type: "mcq", src: "New", q: "For which \\(k\\) does \\(\\left[\\begin{array}{cc|c}1&2&1\\\\0&k-3&4\\end{array}\\right]\\) have no solution?", opts: ["\\(k=3\\)", "\\(k=4\\)", "\\(k=0\\)", "never"], ans: 0,
          why: "If \\(k=3\\) the last row reads \\(0=4\\): impossible. B and C still leave a pivot \\(k-3\\ne0\\), so the system has one solution; D misses the critical value." },
        { type: "free", src: "Sheet 1 · Ex 9", q: "Solve \\(x+y+z=6,\\ y+z=5,\\ z=3\\). Write your working.",
          key: "Already in echelon form, so back-substitute: \\(z=3\\), then \\(y=5-3=2\\), then \\(x=6-2-3=1\\). Solution \\((1,2,3)\\)." }
      ]
    },
    {
      n: 2, name: "Matrix operations",
      syllabus: [
        "Sum: same size, entry by entry",
        "\\(A_{m\\times n}B_{n\\times p}\\) → size \\(m\\times p\\)",
        "\\((AB)_{ij}\\) = row \\(i\\) of \\(A\\) · column \\(j\\) of \\(B\\)",
        "\\(AB\\ne BA\\) in general",
        "\\((AB)^T=B^TA^T\\)"
      ],
      lead: "A product only exists when the inner sizes match. Each entry of \\(AB\\) is one row of \\(A\\) times one column of \\(B\\), and the order matters.",
      defs: [
        ["Size rule", "\\(A\\) is \\(m\\times n\\) and \\(B\\) is \\(n\\times p\\): the inner \\(n\\) must match, the result is \\(m\\times p\\)."],
        ["Entry \\((i,j)\\)", "\\((AB)_{ij}=a_{i1}b_{1j}+a_{i2}b_{2j}+\\dots+a_{in}b_{nj}\\)."]
      ],
      trap: "Matrix product is not commutative. \\(AB\\) and \\(BA\\) usually differ, and one of them may not even exist.",
      worked: {
        title: "Compute AB",
        math: "\\[\\begin{bmatrix}1&2\\\\3&4\\end{bmatrix}\\begin{bmatrix}0&1\\\\1&0\\end{bmatrix}=\\begin{bmatrix}1\\cdot0+2\\cdot1&1\\cdot1+2\\cdot0\\\\3\\cdot0+4\\cdot1&3\\cdot1+4\\cdot0\\end{bmatrix}=\\begin{bmatrix}2&1\\\\4&3\\end{bmatrix}\\]",
        steps: ["Row 1 × column 1, row 1 × column 2, and so on.", "Multiplying on the right by this matrix swaps the columns."]
      },
      ex: [
        { type: "mcq", src: "Sheet 2 · Ex 1", q: "\\(A\\) is \\(2\\times3\\) and \\(B\\) is \\(3\\times4\\). The size of \\(AB\\) is…", opts: ["\\(2\\times4\\)", "\\(3\\times3\\)", "\\(4\\times2\\)", "undefined"], ans: 0,
          why: "Inner sizes match (3 and 3), outer sizes give \\(2\\times4\\). B keeps the inner sizes; C is the size of \\((AB)^T\\); D would be right for \\(BA\\)." },
        { type: "mcq", src: "Sheet 2 · Ex 4", q: "\\(\\begin{bmatrix}1&0\\\\2&1\\end{bmatrix}\\begin{bmatrix}1&3\\\\0&1\\end{bmatrix}=\\)", opts: ["\\(\\begin{bmatrix}1&3\\\\2&7\\end{bmatrix}\\)", "\\(\\begin{bmatrix}1&3\\\\2&6\\end{bmatrix}\\)", "\\(\\begin{bmatrix}7&3\\\\2&1\\end{bmatrix}\\)", "\\(\\begin{bmatrix}1&0\\\\0&1\\end{bmatrix}\\)"], ans: 0,
          why: "Row 2 × column 2: \\(2\\cdot3+1\\cdot1=7\\). B forgets the \\(1\\cdot1\\) term; C is \\(BA\\), the order swapped; D multiplies entry by entry." },
        { type: "mcq", src: "New", q: "\\((AB)^T\\) is equal to…", opts: ["\\(A^TB^T\\)", "\\(B^TA^T\\)", "\\(BA\\)", "\\(AB\\)"], ans: 1,
          why: "Transposing reverses the order: \\((AB)^T=B^TA^T\\). A keeps the order, the most common mistake; C and D forget the transposes." },
        { type: "free", src: "Sheet 2 · Ex 6", q: "Compute \\(\\begin{bmatrix}2&1\\\\0&3\\end{bmatrix}\\begin{bmatrix}1\\\\4\\end{bmatrix}\\).",
          key: "\\(2\\times2\\) times \\(2\\times1\\) gives \\(2\\times1\\). Row 1: \\(2\\cdot1+1\\cdot4=6\\). Row 2: \\(0\\cdot1+3\\cdot4=12\\). Result \\(\\begin{bmatrix}6\\\\12\\end{bmatrix}\\)." }
      ]
    },
    {
      n: 3, name: "Inverse of a matrix",
      syllabus: [
        "\\(AA^{-1}=A^{-1}A=I\\); square matrices only",
        "2×2: \\(\\frac{1}{ad-bc}\\begin{bmatrix}d&-b\\\\-c&a\\end{bmatrix}\\), needs \\(ad-bc\\ne0\\)",
        "Gauss–Jordan: \\([A\\,|\\,I]\\to[I\\,|\\,A^{-1}]\\)",
        "Zero row on the left ⇒ not invertible",
        "\\((AB)^{-1}=B^{-1}A^{-1}\\)"
      ],
      lead: "For a \\(2\\times2\\) matrix use the formula: swap the diagonal, change the sign of the other two, divide by the determinant. For bigger ones, row reduce \\([A\\,|\\,I]\\).",
      defs: [
        ["2×2 formula", "\\(\\begin{bmatrix}a&b\\\\c&d\\end{bmatrix}^{-1}=\\dfrac{1}{ad-bc}\\begin{bmatrix}d&-b\\\\-c&a\\end{bmatrix}\\)"],
        ["Gauss–Jordan", "Apply to \\(I\\) the same row operations that turn \\(A\\) into \\(I\\); what \\(I\\) becomes is \\(A^{-1}\\)."]
      ],
      trap: "The inverse of a product reverses the order, exactly like the transpose: \\((AB)^{-1}=B^{-1}A^{-1}\\).",
      worked: {
        title: "Invert a 2 × 2 matrix",
        math: "\\[\\det A=2\\cdot3-1\\cdot5=1,\\qquad A^{-1}=\\begin{bmatrix}3&-1\\\\-5&2\\end{bmatrix}\\]",
        steps: ["Swap 2 and 3, change the signs of 1 and 5.", "Divide by \\(\\det A=1\\).", "Check: \\(AA^{-1}=I\\)."]
      },
      ex: [
        { type: "mcq", src: "Sheet 3 · Ex 2", q: "The inverse of \\(\\begin{bmatrix}1&2\\\\3&7\\end{bmatrix}\\) is…", opts: ["\\(\\begin{bmatrix}7&-2\\\\-3&1\\end{bmatrix}\\)", "\\(\\begin{bmatrix}7&2\\\\3&1\\end{bmatrix}\\)", "\\(\\begin{bmatrix}1&-2\\\\-3&7\\end{bmatrix}\\)", "\\(\\begin{bmatrix}-7&2\\\\3&-1\\end{bmatrix}\\)"], ans: 0,
          why: "\\(\\det=7-6=1\\), swap the diagonal and negate the rest. B forgets the signs; C forgets to swap the diagonal; D uses \\(\\det=-1\\)." },
        { type: "mcq", src: "Sheet 3 · Ex 5", q: "Is \\(\\begin{bmatrix}2&4\\\\1&2\\end{bmatrix}\\) invertible?", opts: ["No, its determinant is 0", "Yes, its determinant is 8", "Yes, its determinant is 4", "Only if we swap the rows"], ans: 0,
          why: "\\(2\\cdot2-4\\cdot1=0\\), and the rows are proportional. B adds instead of subtracting; C only multiplies the diagonal; D: swapping rows only changes the sign of the determinant." },
        { type: "mcq", src: "New", q: "\\((AB)^{-1}\\) is equal to…", opts: ["\\(A^{-1}B^{-1}\\)", "\\(B^{-1}A^{-1}\\)", "\\(BA\\)", "\\((BA)^{-1}\\)"], ans: 1,
          why: "\\((AB)(B^{-1}A^{-1})=A(BB^{-1})A^{-1}=I\\). A keeps the order; D equals \\(A^{-1}B^{-1}\\), the same mistake in disguise." },
        { type: "free", src: "Sheet 3 · Ex 8", q: "Find the inverse of \\(\\begin{bmatrix}3&1\\\\2&1\\end{bmatrix}\\) and check it.",
          key: "\\(\\det=3-2=1\\). Inverse \\(\\begin{bmatrix}1&-1\\\\-2&3\\end{bmatrix}\\). Check: \\(\\begin{bmatrix}3&1\\\\2&1\\end{bmatrix}\\begin{bmatrix}1&-1\\\\-2&3\\end{bmatrix}=\\begin{bmatrix}1&0\\\\0&1\\end{bmatrix}\\)." }
      ]
    },
    {
      n: 4, name: "Determinants",
      syllabus: [
        "2×2: \\(\\det=ad-bc\\)",
        "3×3: Laplace expansion along a row or column",
        "Triangular: product of the diagonal",
        "Row swap → sign flips; \\(L_i+\\alpha L_j\\) → unchanged",
        "\\(\\det(kA)=k^n\\det A\\) for \\(n\\times n\\)",
        "\\(\\det(AB)=\\det A\\det B\\); invertible ⇔ \\(\\det\\ne0\\)"
      ],
      lead: "The determinant is one number that tells you if a square matrix is invertible. Expand along the row or column with the most zeros, or row reduce to a triangle first.",
      defs: [
        ["Laplace expansion", "\\(\\det A=\\sum_j (-1)^{i+j}a_{ij}\\det A_{ij}\\), signs in a chessboard pattern \\(+\\,-\\,+\\)."],
        ["Row operations", "Swap: sign changes. Multiply a row by \\(\\alpha\\): det multiplied by \\(\\alpha\\). Add a multiple of a row: no change."]
      ],
      trap: "\\(\\det(2A)\\) is not \\(2\\det A\\): every one of the \\(n\\) rows is multiplied by 2, so it is \\(2^n\\det A\\).",
      worked: {
        title: "Expand along row 1",
        math: "\\[\\begin{vmatrix}2&0&1\\\\1&3&2\\\\0&1&4\\end{vmatrix}=2\\begin{vmatrix}3&2\\\\1&4\\end{vmatrix}-0+1\\begin{vmatrix}1&3\\\\0&1\\end{vmatrix}=2\\cdot10+1\\cdot1=21\\]",
        steps: ["The zero in position (1,2) kills one term.", "Signs follow \\(+\\,-\\,+\\) along the row."]
      },
      ex: [
        { type: "mcq", src: "Sheet 4 · Ex 1", q: "\\(\\begin{vmatrix}3&5\\\\1&2\\end{vmatrix}=\\)", opts: ["1", "11", "−1", "6"], ans: 0,
          why: "\\(3\\cdot2-5\\cdot1=1\\). B adds the products; C subtracts in the wrong order; D only multiplies the diagonal." },
        { type: "mcq", src: "Sheet 4 · Ex 6", q: "\\(A\\) is \\(3\\times3\\) with \\(\\det A=2\\). Then \\(\\det(2A)=\\)", opts: ["4", "16", "8", "6"], ans: 1,
          why: "\\(2^3\\cdot2=16\\). A multiplies by 2 once; C forgets \\(\\det A\\); D multiplies by 3 instead of raising to the power 3." },
        { type: "mcq", src: "New", q: "\\(\\begin{vmatrix}2&7&1\\\\0&3&5\\\\0&0&-1\\end{vmatrix}=\\)", opts: ["−6", "6", "4", "0"], ans: 0,
          why: "Triangular, so multiply the diagonal: \\(2\\cdot3\\cdot(-1)=-6\\). B drops the sign; C adds the diagonal; D: a zero entry does not make the determinant zero." },
        { type: "free", src: "Sheet 4 · Ex 9", q: "Compute \\(\\begin{vmatrix}1&2&0\\\\0&1&3\\\\2&0&1\\end{vmatrix}\\).",
          key: "Along row 1: \\(1\\cdot(1\\cdot1-3\\cdot0)-2\\cdot(0\\cdot1-3\\cdot2)+0=1+12=13\\)." }
      ]
    },
    {
      n: 5, name: "Independence, span and bases",
      syllabus: [
        "Combination: \\(c_1\\mathbf v_1+\\dots+c_k\\mathbf v_k\\)",
        "Span: the set of all combinations",
        "Independent ⇔ only \\(c_i=0\\) gives \\(\\mathbf 0\\)",
        "Test: vectors as columns, a pivot in every column ⇔ independent",
        "More than \\(n\\) vectors in \\(\\mathbb R^n\\) ⇒ dependent",
        "Basis = independent + spans; \\(n\\) vectors in \\(\\mathbb R^n\\) with \\(\\det\\ne0\\)"
      ],
      lead: "Put the vectors as columns and row reduce. A pivot in every column means independent; a pivot in every row means they span. Both at once means a basis.",
      defs: [
        ["Independent", "\\(c_1\\mathbf v_1+\\dots+c_k\\mathbf v_k=\\mathbf 0\\) only when every \\(c_i=0\\). Equivalently, no vector is a combination of the others."],
        ["Basis of \\(\\mathbb R^n\\)", "Exactly \\(n\\) independent vectors. For a square matrix of them: basis ⇔ \\(\\det\\ne0\\)."]
      ],
      trap: "Independent does not mean \"no vector is a multiple of another\". Three vectors can be pairwise non-proportional and still dependent, like \\(\\mathbf v_3=\\mathbf v_1+\\mathbf v_2\\).",
      worked: {
        title: "Are (1, 2) and (3, 6) independent?",
        math: "\\[(3,6)=3\\cdot(1,2)\\qquad\\Rightarrow\\qquad 3\\mathbf v_1-\\mathbf v_2=\\mathbf 0\\]",
        steps: ["A non-zero combination gives \\(\\mathbf 0\\): dependent.", "Same answer with the determinant: \\(1\\cdot6-3\\cdot2=0\\)."]
      },
      ex: [
        { type: "mcq", src: "Sheet 5 · Ex 2", q: "\\((1,0,1),(0,1,1),(1,1,2)\\) are…", opts: ["dependent", "independent", "a basis of \\(\\mathbb R^3\\)", "impossible to tell"], ans: 0,
          why: "The third is the sum of the first two. B and C miss that because no two vectors are proportional (the trap above); D: one row reduction answers it." },
        { type: "mcq", src: "New", q: "Four vectors in \\(\\mathbb R^3\\) are…", opts: ["always dependent", "always independent", "independent if none is zero", "a basis"], ans: 0,
          why: "At most 3 pivots for 4 columns, so a free variable always exists. C is a necessary condition, never a sufficient one; D: a basis of \\(\\mathbb R^3\\) has exactly 3 vectors." },
        { type: "mcq", src: "Sheet 5 · Ex 7", q: "Do \\((1,2)\\) and \\((2,5)\\) form a basis of \\(\\mathbb R^2\\)?", opts: ["Yes, the determinant is 1", "No, the determinant is 0", "No, 2 vectors are not enough", "Yes, but only with a third vector"], ans: 0,
          why: "\\(1\\cdot5-2\\cdot2=1\\ne0\\). B miscalculates; C: 2 is exactly the dimension of \\(\\mathbb R^2\\); D: a third vector would make them dependent." },
        { type: "free", src: "Sheet 5 · Ex 4", q: "Write \\((5,8)\\) as a combination of \\((1,2)\\) and \\((1,1)\\).",
          key: "\\(a(1,2)+b(1,1)=(5,8)\\) gives \\(a+b=5\\) and \\(2a+b=8\\). Subtract: \\(a=3\\), then \\(b=2\\). So \\((5,8)=3(1,2)+2(1,1)\\)." }
      ]
    }
  ],
  /* Study plan: day index → sessions. t = topic number (0 = mixed), a = action, h = hours */
  plan: [
    [{t:1,a:"Learn",h:1},{t:1,a:"Exercises",h:1}],
    [{t:1,a:"Review",h:.5},{t:2,a:"Learn",h:1},{t:2,a:"Exercises",h:.5}],
    [{t:2,a:"Review",h:.5},{t:3,a:"Learn",h:1},{t:3,a:"Exercises",h:1}],
    [{t:1,a:"Review",h:.5},{t:3,a:"Review",h:.5},{t:4,a:"Learn",h:1},{t:4,a:"Exercises",h:1}],
    [{t:2,a:"Review",h:.5},{t:4,a:"Review",h:.5},{t:5,a:"Learn",h:1},{t:5,a:"Exercises",h:1}],
    [{t:3,a:"Review",h:.5},{t:5,a:"Review",h:.5},{t:0,a:"Catch-up buffer",h:1}],
    [{t:4,a:"Review",h:.5},{t:4,a:"Exercises",h:.5},{t:0,a:"Mixed exercises 1–3",h:1}],
    [{t:1,a:"Review",h:.5},{t:5,a:"Review",h:.5},{t:0,a:"Mixed exercises 3–5",h:1}],
    [{t:2,a:"Review",h:.5},{t:0,a:"Redo missed questions",h:1.5}],
    [{t:3,a:"Review",h:.5},{t:4,a:"Review",h:.5},{t:5,a:"Review",h:.5},{t:0,a:"Mock test",h:1.5}]
  ]
};

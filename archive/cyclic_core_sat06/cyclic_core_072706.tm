<TeXmacs|WinTeXmacs-1.0.5>

<style|article>

<\body>
  <assign|tmem|<macro|1|<with|font-shape|italic|<arg|1>>>><assign|tmstrong|<macro|1|<with|font-series|bold|<arg|1>>>><assign|tmop|<macro|1|<ensuremath|<with|math-font-family|rm|<arg|1>>>>><assign|tmfloatcontents|<macro|>><assign|tmfloat|<\macro|1|2|3|4|5>
    <assign|tmfloatcontents|<macro|<arg|4>>>
    <setlength|<tmfloatwidth>|<widthof|<tmfloatcontents>>+1in>
    <if|<equal|<arg|2>|small>|<if|<lengthtest|<tmfloatwidth> \<gtr\>
    <linewidth>>|<setlength|<tmfloatwidth>|<linewidth>>|>|<setlength|<tmfloatwidth>|<linewidth>>>\ 

    <\minipage>
      [<arg|1>]<tmfloatwidth>

      <center|<tmfloatcontents> <captionof|<arg|3>|<arg|5>>>
    </minipage>
  </macro>>

  <surround| \ ||<doc-data|<doc-title|Cyclic Core Covering and Finite Cubical
  Cell Complexes>|<\doc-author-data|<author-name|Alan J. Coppola and Richard
  Weiss<next-line>OptNgn Software, LLC and The Evergreen State College
  >|<\author-address>
    ajjc@optngn.com and weissr@evergreen.edu
  </author-address>>
    \;
  <|doc-author-data>
    \;
  <|doc-author-data>
    \;
  </doc-author-data>|<doc-date|<inactive|<date|July 27, 2006>>>>>

  <\abstract>
    In this paper, we improve the standard branch-and-bound algorithm for
    finding a minimum cover by addressing the cyclic-core processing. We show
    how a covering problem such as two-level logic minimization can be
    represented as a finite cubical cell complex, which encodes topological
    information that aids the minimization process. The paper shows that by
    extending the covering table so that it also represents the implicitly
    defined combinatorial finite cubical cell complex of a covering problem,
    any resulting cyclic-core covering sub-problems, with collapsible cells,
    can be exactly solved using only one recursive call instead of two. The
    new covering table operation, called collapse, arises from the concepts
    of cell collapse and expansion from simple homotopy theory in topolgy. A
    collapsible cell of the cyclic core allows the two recursive calls
    (cell-in and cell-out) to be encoded into one call. This reduces the
    number of recursive computations needed to solve the minimal covering
    problem.
  </abstract>

  <section|Introduction>

  Covering problems are typically solved using branch and bound algorithms,
  by realizing them in tabular form, followed by iterative reduction of the
  table by removing columns and rows through a small set of fixed operations.
  This process terminates when all of the rows have been eliminated
  indicating that all of the cells have been covered. The columns correspond
  to prime implicants and the ones that have been removed in this process
  form the minimal cover. However, the operations that are usually applied
  can result in a situation called a cyclic core, where the problem is split
  into two subproblems of equal size and each one is solved independently.
  Our goal is to create an operation which produces a single subproblem that
  is roughly the same size as each of the other subproblems, and thus, we cut
  the amount of computation for that step in half.

  The standard table operations that are used to produce the minimal cover
  are essentiality, row dominance, column dominance and Gimpel's transform.
  [2] They depend on finding essential prime implicants, followed by row and
  column reductions. An essential prime implicant contains a min-term that is
  not covered by any other prime implicant. A fixed-point occurs if the
  operations do not change the table after each application even though the
  algorithm has not terminated. This occurs when there are no essential prime
  implicants, or dominated elements, and the configuration is called a cyclic
  core. The step that is usually applied is to choose a column (prime
  implicant) and generate two instances of the problem: one in which the
  prime implicant is part of the minimal cover, and one in which it is not.
  Each of these subproblems can then be solved recursively using the branch
  and bound method with the standard table operations.

  Our approach is based on the intuition that the table representation is
  omitting information that is present in the cube complex, which is a
  natural representation of the original two-level logic minimization
  problem. The cube complex is a set of cubes of various dimensions with the
  property that if they intersect, then the intersect in a set of faces which
  are also cubes. All of these cubes can be viewed as subsets of a cube whose
  dimension is the number of variables in the logical expression to be
  minimized. [1], [5]

  Most recent work on the covering problems have attacked finding and
  applying the lower bounds found to prune the search space for the minimal
  solution. [6-9] This paper introduces a different method for pruning the
  search space, based on an encoding used for special cells in the cyclic
  core. The identification and of these cells allows one recursive call
  instead of two to solve a cyclic core subproblem. This is our contribution.

  We prove a theorem which shows that given the cyclic-core of a minimization
  problem, there is a special type of cube, a collapsible cube, to branch on,
  such that the minimum cover can be found with a single recursive call. We
  present an example of a cubical cell complex representation, and
  corresponding minimization.

  <section|Definitions and Background>

  <subsection|Cubical Cell Complexes, Combinatorial Topology, and Covering>

  The cubical cell complex provides a general framework in which to represent
  minimal covering problems, higher-order connectivity, cycles of any
  dimension, and geometric visualization of optimization problems.

  For the purposes of this paper, we specialize to cubes and cubical
  complexes, even though the techniques can be generalized to cells and
  abstract cell complexes.

  <\definition>
    A <em|cubical complex> C = (Skel, <with|mode|math|\<leq\>,dim>
    \<leqslant\> \<leqslant\>) consists of:

    <\itemize>
      <item>A collection of cubes Skel of
      <with|mode|math|<with|math-font|Bbb*|B><with|mode|text|<rsup|k>><with|mode|text|>>,
      each of which is called a cube of C, and a partial order
      <with|mode|math|\<leq\>>, which captures the face relations of C.

      <item>A <em|<em|closure under intersection property> <em|>> for Skel
      (if a, b <with|mode|math|\<epsilon\>> Skel, then a
      <with|mode|math|\<wedge\>>b <with|mode|math|\<varepsilon\>> Skel)

      <item>A <em|face closure property> <strong|> for Skel (if a
      <with|mode|math|\<epsilon\>> Skel, and b <with|mode|math|\<leq\>a> then
      b <with|mode|math|\<varepsilon\>> Skel )

      <item>A dimension function (There is a function <with|mode|math|dim
      :Skel\<longrightarrow\><with|math-font|Bbb*|N>suchthatdim
      (pt)=0,andifb\<leq\>a,then>dim(b)<with|mode|math|\<leq\>dim (a)>
    </itemize>
  </definition>

  <\definition>
    L is a sub-complex of K if L is a cubical complex, each of whose faces
    are faces of K. For example, if L<rsup|i >=
    <with|mode|math|{c\<epsilon\>Skel\|dim (c)\<leqslant\>i}>, then L<rsup|i
    > is the sub-complex called the i-skeleton of C.
  </definition>

  <\definition>
    Let C be a cubical cell complex. Let c be a cell of C. c is said to be
    collapsible if c has a face f <with|mode|math|\<leq\>c>, such that dim(f)
    <with|mode|math|=dim (c)-1,>and f is not a face of q, for all q
    <with|mode|math|\<epsilon\>> C. f is also called a free face of c.
  </definition>

  The concept of cellular collapses and expansions comes from simple homotopy
  theory of topology. In this context it also captures a generalization of
  essential prime because for a cell to be collapsible, it must have a free
  face, i.e. one that is not shared. [4], [5]

  <\definition>
    If K and L are cubical cell complexes, we say that there is an elementary
    cell collapse from K to L (K<with|mode|math|\<searrow\>L>), if K = L
    <with|mode|math|\<cup\>e,whereeisacellofK>, with free face f not a face
    of any other face of L. The cell e is said to be a collapsible cell.
    Note: This is equivalent to the existence of a homotopy from K to L.
    Also, L is said to expand to K (L<with|mode|math|\<nearrow\>K>).
  </definition>

  <section|Minimization Process>

  <subsection|Exact Two-Level Boolean Minimization [2]>

  The object of this classical problem is given a boolean function f, find an
  exact minimum size representation of f as a sum-of-products cube
  representation of f. The usual method is:

  <\theorem>
    Given a sum-of-products boolean function f, the minimum cost
    representation of f as a sum of products is found by iteratively applying
    steps 1-4.
  </theorem>

  <\enumerate-numeric>
    <item*|FindPrimes>Find all the prime implicants of f

    <item*|CreateCov>Create the covering matrix of the primes of f, where the
    columns are the primes and the rows are the minterms of f.

    <item*|Reduction>Perform reductions on the covering matrix, until a fixed
    point table, called the cyclic-core is reached. The table reductions are:
    [2],[3]

    <\enumerate-roman>
      Partitioning (i.e. finding the conected components), iteratively
      followed by:

      <\itemize-dot>
        <item>Essentials reduction by choosing cubes which are essentials to
        be in the minimal cost cover.

        <item>Row dominance - a strongly equivalent operation (no solutions
        are eliminated [2])

        <item>Column dominance - a weakly equivalent operation (some
        solutions are eliminated, but a minimum is not [2])
      </itemize-dot>
    </enumerate-roman>

    <item*|SolveCyclicCore>Recursively solve the cyclic-core problem by
    choosing a column(prime) to assume is first in the cover, find a
    recursive solution, and then is not in the cover, find a recursive
    solution to that problem, and then pick the cover that has the least
    number of elements as the minimal cover. Sophisticated branch and bound
    techniques, involving choosing a maximal independent set of elements at
    each cyclic-core step which can be used to create a series of lower
    bounds on which to prune the recursions. See [6],[7],[8],[9].

    The method we propose will enhance Step 4, by allowing a single recursive
    call in the case that a free face is found.
  </enumerate-numeric>

  <subsection|Cyclic Core Reduction Overview >

  We assume that the cell complex is represented either explicitly or
  implicitly, and that no computation of faces or intersections are explicity
  done unless needed. i.e. lazy evaluation is used. For example, an explicit
  initial representation would be a list of cubes of varying dimensions. An
  implicit representation would be as a BDD.

  During the exact minimization algorithm outlined in Section 3.2, the list
  of cubes can grow and shrink. We assume that the prime cube complex is
  given, and that the covering table is replaced by a choice pairing function
  Pair<rsub|f>(cube, prime) = 1 <with|mode|math|\<Leftrightarrow\>cube\<leqslant\>prime>
  . This allows us to view a covering table a view of the cubical complex. No
  face information is lost. This is key in allowing us to compute the
  collapsible cubes necessary to reduce the cyclic core resursively.

  <section|Description of Algorithm>

  =number of vertices(minterms) of C(f).

  Each cube will correspond to a row of the covering table, and each column
  corresponds to a prime cube of the cubical complex, which lives in a
  universe which is the smallest dimensional cube containing all the cubes of
  the cubical complex.

  The graded table is a view of the cubical cell complex and can be derived
  from it. Restated, the minimal covering problem is to find a set of columns
  of TC which cover C, and has minimal cost. The contribution of this paper
  is two-fold: to use the cubical cell complex directly as the representation
  of the combinatorial minimization problem, and to show how this
  representation allows the introduction of a new reduction method during the
  cyclic core recursive solution.

  The covering problem is to find a minimum set of columns of T<rsub|C> which
  cover C, and has minimal cost.

  The new contribution of this paper is two-fold: to introduce cell complexes
  as a natural representation of combinatorial problems, and to show how this
  representation allows the introduction of a new reduction method during the
  cyclic-core recursive solution.

  <subsection|Finding a collapsible cell.>

  With the representation we have chosen, finding collapsible cubes is like
  finding essential cubes. Consider a top dimensional cell c, of dimension k.
  Then a cube with a free face is one where the set of k-dimensional cubes
  other than c intersected with c does not cover the faces of c. The faces of
  c not covered by these k-dimensional cells are the free faces. Note that
  the analogous step for essential primes is the first step in the classical
  Quine-McCluskey algorithm.

  <subsection|Collapsible Element Reduction>

  Given an implicit or explicit representation of the initial cubical
  complex, we allow the addition of cells to the complex, when necessary, to
  solve the covering problem. Most additions result from intersecting cells
  when computing the set of primes or in finding the collapsible cells.

  <\theorem>
    The [CyclicCore] step of Theorem 5 can be replaced by the
    [CyclicCoreCollapse] step, and maintain cover cost minimality.

    [CyclicCoreCollapse] If a collapsible element exists, removing the
    element p, and replace it with the set of free faces of p, perform a
    single recursive call of the modified minimization algorithm, if any of
    the added faces are in the returned cover, remove them, and add p back
    in. If there are no collapsible faces, perform the [CyclicCore] step of
    Theorem 5. So the Theorem 5 usual algorithm is not modified unless there
    are collapsible cells, in which case columns are temporarily removed and
    added during the course of the minimization.

    <\proof>
      \;
    </proof>

    This involves, at the graded covering matrix level, removing the column
    p, and replacing it with a set of one dimensional less columns which are
    the free faces of p, FreeFaces(p).

    Recursively continue to apply the non cyclic-core reductions, followed by
    the cyclic-core collapsible reduction, along with chosing a face of the
    the most recently used collapsible cube processed when a sub cyclic core
    has no collapsible cubes in it, a<em|<em|>>nd return with a cover
    CollapseCov.

    Claim: CollapseCov, or CollapseCovPlus = ReducedCov(CollapseCov + p) is
    the absolute minimum cost cover of the row elements by the column sets,
    where ReducedCov simply takes a cover and makes it irredundant.

    Let FreeSize = <with|mode|math|\|CollapseCov\<wedge\>FreeFaces(p)\|>. To
    complete the proof, consider the following cases:

    <\enumerate-roman>
      <item>FreeSize <with|mode|math|=0,>

      If FreeSize <with|mode|math|=0,> then CollapseCov is the minimum, as it
      didn't use any of the added free face cells, hence only used the
      original cells to cover the rows, and, so corresponds to the case that
      the collapsible cube was not included initially, whereas, by including
      the free faces, the opportunity was presented to the minimization
      algorithm to use them to get a solution with lesser cost, so if a cover
      of lesser cost existed with some of the free faces of p in it, then it
      would have been found.

      <item>FreeSize <with|mode|math|\<geqslant\>1,>

      Then CollapseCovPlus is the minimum, as the expansion of the cube in
      the direction of one of the free faces returned keeps the cost the
      same, or better, if the cost function is dimension dependent.
      <em|<em|>> Then CollapseCovPlus is the minimum, and will have a cost
      less than or equal to the cost of CollapseCov, as if all the returned
      faces are removed, we have a minimum cover of the original Cyclic Core
      by primes, which can be at most one less element in cost from the case
      when the cube is originally included in the minimal cover, and then
      minimized. This returned encoding corresponds to having the original
      cube p in the minimal cover.
    </enumerate-roman>
  </theorem>

  <section|Realization Considerations>

  State of the art unate covering tools are embodied in the tools Eclipse,
  Aura-II, Scherzo, and Espresso-Signature-Exact. [2, 6-9] To implement the
  concepts in this paper, the techniques should be added to one of the above
  code bases, and compared to the others on suites of examples, as was done
  in Eclipse and Aura-II.

  It is an open question as to whether the proof given in this paper can be
  extended to the case of encoding all of the collapsible cubes
  simultaneously, as a single step, and then continuing with the algorithm
  recursively. This type of operation would correspond to shelling the cyclic
  core by collapsing it's boundary all at once, and then recursively
  continuing with that process.

  <section|Conclusions and Future Work>

  In this paper, it was shown first, how to identify special cubes, called
  collapsible ones, in the cyclic core covering problem, and second how to
  use them to modify the branch part of the branch and bound algorithm, which
  allows a minimum cost solution to be found with a single recursion, at the
  cost of encoding the collapsible cubes by their free faces, and by
  maintaining the structur<space|20>e of the cubical cell complex, as the
  minimization proceeds.

  In future work, we plan to generalize the current approach for cubical cell
  complexes. We believe that binate covering problems, MaxCostSAT and other
  problem areas can also be addressed using these methods.

  <section|References>

  [1] J.P. Roth, ``Algebraic topological methods for the synthesis of
  switching systems I``, Trans. Am. Math. Soc., Vol. 88, No. 2, pp301-32.

  [2] O. Courdert, ``Two-level logic minimization: and overview'',
  Integration, the VLSI Journal, 17-2, pp. 97-140, October 1994.

  [3] O. Coudert. On solving binate covering problems. In The Proceedings of
  the Design Automation Conference, pages 197-- 202, June 1996.

  [4] M.M. Cohen, A Course in Simple-Homotopy Theory, Springer-Verlag, New
  York, 1973

  [5] A. J. Coppola, ``New methods in the analysis of logic minimization data
  and algorithms'', Proceedings of the 26th Design Automation Conference,
  June, 1989.

  [6] X.Y. Li, M.F. Stallmann, and F. Brglez. A local search solver using an
  e®ective switching strategy and an e±cient unit propagation. Lecture Notes
  in Computer Science, 2919:53 { 68, 2004. For links to re-prints, data sets
  and experimental testbed, see also http://www.cbl.ncsu.edu/publications/.

  [7] E. I. Goldberg, L. P. Carloni, T. Villa, R. K. Brayton, and A. L.
  Sangiovanni-Vincentelli. Negative Thinking in Branch-and-Bound: the Case of
  Unate Covering. IEEE Transactions on Computer-Aided Design, 19(3):281--294,
  Mar. 2000.

  [8] C. Plessl and M. Platzner, ``Instance-Specific Accelerators for Minimum
  Covering'', Proceedings of the 1st International Conference on Engineering
  of Reconfigurable Systems and Algorithms (ERSA) } , pp. 85--91, 2001, Las
  Vegas, Nevada, USA, June, CSREA Press }

  [9] Samir Sapra, Michael Theobald, Edmund M. Clarke, ``SAT-Based Algorithms
  for Logic Minimization'', ICCD, 2003,pp. 510-515

  <\example>
    Cyclic Core Example

    If Figure 1 represents the geometric realization of a cyclic core, then
    any of the primes 1-6 are collapsible. Table 1 represents the face
    incidence relation, from which the graded table can be generated. Each 1
    in the table refers to the fact that the row cell intersects the column
    prime(which in this case also corresponds to a row cell) in one lower
    dimensional face.

    If cell c<rsup|2><rsub|1> is chosen as the collapsible cell, then it is
    removed, and the 1 dimesional cell on the outside, between cells 6 and 2
    replaces it. Note that there are now three additional free faces, and the
    complex is still a cyclic core. Proceeding recursively, the whole one
    skeleton is outlined, until finally the recursion is broken, and the
    process quickly pops back up to the beginning, at each stage choosing a
    sequence of primes wich minimally cover S.
  </example>

  <space|fill>

  <\multicols|2>
    \ <tmfloat|h|small|table|<space|fill> <space|fill>
    <space|fill><tabular*|<tformat|<cwith|1|-1|1|1|cell-lborder|1ln>|<cwith|1|-1|1|1|cell-halign|l>|<cwith|1|-1|1|1|cell-rborder|1ln>|<cwith|1|-1|2|2|cell-halign|l>|<cwith|1|-1|2|2|cell-rborder|1ln>|<cwith|1|-1|3|3|cell-halign|l>|<cwith|1|-1|3|3|cell-rborder|1ln>|<cwith|1|-1|4|4|cell-halign|l>|<cwith|1|-1|4|4|cell-rborder|1ln>|<cwith|1|-1|5|5|cell-halign|l>|<cwith|1|-1|5|5|cell-rborder|1ln>|<cwith|1|-1|6|6|cell-halign|l>|<cwith|1|-1|6|6|cell-rborder|1ln>|<cwith|1|-1|7|7|cell-halign|l>|<cwith|1|-1|7|7|cell-rborder|1ln>|<cwith|1|-1|8|8|cell-halign|l>|<cwith|1|-1|8|8|cell-rborder|1ln>|<cwith|1|-1|9|9|cell-halign|l>|<cwith|1|-1|9|9|cell-rborder|1ln>|<cwith|1|-1|10|10|cell-halign|l>|<cwith|1|-1|10|10|cell-rborder|1ln>|<cwith|1|1|1|-1|cell-tborder|1ln>|<cwith|1|1|1|-1|cell-bborder|1ln>|<cwith|2|2|1|-1|cell-bborder|1ln>|<cwith|3|3|1|-1|cell-bborder|1ln>|<cwith|4|4|1|-1|cell-bborder|1ln>|<cwith|5|5|1|-1|cell-bborder|1ln>|<cwith|6|6|1|-1|cell-bborder|1ln>|<cwith|7|7|1|-1|cell-bborder|1ln>|<cwith|8|8|1|-1|cell-bborder|1ln>|<cwith|9|9|1|-1|cell-bborder|1ln>|<cwith|10|10|1|-1|cell-bborder|1ln>|<table|<row|<cell|
    >|<cell| p<rsub|1> >|<cell| p<rsub|2> >|<cell| p<rsub|3> >|<cell|
    p<rsub|4> >|<cell| p<rsub|5> >|<cell| p<rsub|6> >|<cell| p<rsub|7>
    >|<cell| p<rsub|8> >|<cell| p<rsub|9>>>|<row|<cell|<tabular*|<tformat|<cwith|1|-1|1|1|cell-halign|l>|<table|<row|<cell|
    c<rsup|2><rsub|1> >>>>> >|<cell| >|<cell| 1 >|<cell| >|<cell| >|<cell|
    >|<cell| 1 >|<cell| >|<cell| >|<cell| 1>>|<row|<cell|c<rsup|2>
    <em|><rsub|2> >|<cell| 1 >|<cell| >|<cell| 1 >|<cell| >|<cell| >|<cell|
    >|<cell| >|<cell| >|<cell| 1>>|<row|<cell|c<em|<rsup|2>><rsub|3> >|<cell|
    >|<cell| 1 >|<cell| >|<cell| 1 >|<cell| >|<cell| >|<cell| >|<cell| 1
    >|<cell| >>|<row|<cell|c<rsup|2><rsub|4> >|<cell| >|<cell| >|<cell| 1
    >|<cell| >|<cell| 1 >|<cell| >|<cell| >|<cell| 1 >|<cell|
    >>|<row|<cell|c<rsup|2><rsub|5> >|<cell| >|<cell| >|<cell| >|<cell| 1
    >|<cell| >|<cell| 1 >|<cell| 1 >|<cell| >|<cell|
    >>|<row|<cell|c<rsup|2><rsub|<rsup|>6> >|<cell| 1 >|<cell| >|<cell|
    >|<cell| >|<cell| 1 >|<cell| >|<cell| 1 >|<cell| >|<cell|
    >>|<row|<cell|c<rsup|2><rsub|7> >|<cell| >|<cell| >|<cell| >|<cell|
    >|<cell| 1 >|<cell| 1 >|<cell| 1 >|<cell| 1 >|<cell|
    >>|<row|<cell|<tabular*|<tformat|<cwith|1|-1|1|1|cell-halign|l>|<table|<row|<cell|
    c<rsup|2><rsub|8> >>>>> >|<cell| >|<cell| >|<cell| 1 >|<cell| 1 >|<cell|
    >|<cell| 1 >|<cell| >|<cell| >|<cell|
    1>>|<row|<cell|<tabular*|<tformat|<cwith|1|-1|1|1|cell-halign|l>|<table|<row|<cell|
    c<rsup|2><rsub|9> >>>>> >|<cell| 1 >|<cell| 1 >|<cell| >|<cell| >|<cell|
    >|<cell| >|<cell| 1 >|<cell| 1 >|<cell| >>>>>|Initial Prime Implicant
    Graded Covering Table for S> <em|>

    <\center>
      <\flushright>
        <tmfloat|h|small|figure|<epsfig|file=>|Cyclic Core Two-Dimensional
        Collapsible Cube Complex S> <space|fill>\ 
      </flushright>
    </center>
  </multicols>
</body>

<\references>
  <\collection>
    <associate|auto-1|<tuple|1|?>>
    <associate|auto-10|<tuple|5|?>>
    <associate|auto-11|<tuple|6|?>>
    <associate|auto-12|<tuple|7|?>>
    <associate|auto-2|<tuple|2|?>>
    <associate|auto-3|<tuple|2.1|?>>
    <associate|auto-4|<tuple|3|?>>
    <associate|auto-5|<tuple|3.1|?>>
    <associate|auto-6|<tuple|3.2|?>>
    <associate|auto-7|<tuple|4|?>>
    <associate|auto-8|<tuple|4.1|?>>
    <associate|auto-9|<tuple|4.2|?>>
  </collection>
</references>

<\auxiliary>
  <\collection>
    <\associate|toc>
      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|1<space|2spc>Introduction>
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-1><vspace|0.5fn>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|2<space|2spc>Definitions
      and Background> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-2><vspace|0.5fn>

      <with|par-left|<quote|1.5fn>|2.1<space|2spc>Cubical Cell Complexes,
      Combinatorial Topology, and Covering
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-3>>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|3<space|2spc>Minimization
      Process> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-4><vspace|0.5fn>

      <with|par-left|<quote|1.5fn>|3.1<space|2spc>Exact Two-Level Boolean
      Minimization [2] <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-5>>

      <with|par-left|<quote|1.5fn>|3.2<space|2spc>Cyclic Core Reduction
      Overview \ <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-6>>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|4<space|2spc>Description
      of Algorithm> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-7><vspace|0.5fn>

      <with|par-left|<quote|1.5fn>|4.1<space|2spc>Finding a collapsible cell.
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-8>>

      <with|par-left|<quote|1.5fn>|4.2<space|2spc>Collapsible Element
      Reduction <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-9>>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|5<space|2spc>Realization
      Considerations> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-10><vspace|0.5fn>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|6<space|2spc>Conclusions
      and Future Work> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-11><vspace|0.5fn>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|7<space|2spc>References>
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-12><vspace|0.5fn>
    </associate>
  </collection>
</auxiliary>
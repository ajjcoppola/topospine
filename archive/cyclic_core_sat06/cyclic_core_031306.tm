<TeXmacs|WinTeXmacs-1.0.5>

<style|<tuple|article|allouche|bpr>>

<\body>
  <doc-data|<doc-title|Cyclic Core Covering and Finite Abstract Cell
  Complexes>|<doc-author-data|<author-name|Alan J. Coppola and Richard
  Weiss>|<\author-address>
    \;
  </author-address>|<\author-address>
    The Evergreen State College

    Olympia, WA 98005
  </author-address>>|<doc-author-data|<author-name|>>>

  <\abstract>
    In this paper, we improve the standard branch-and-bound algorithm for
    finding a minimum cover by addressing the cyclic-core processing. We show
    how a covering problem such as two-level logic minimization can be
    represented as a finite abstract cell complex, which encodes topological
    information that aids the minimization process. The paper shows that by
    extending the covering table so that it also represents the implicitly
    defined combinatorial finite abstract cell complex of a covering problem,
    any resulting cyclic-core covering sub-problems, with collapsible cells,
    can be exactly solved using only one recursive call instead of two. The
    new covering table operation, called collapse, arises from the concepts
    of cell collapse and expansion from simple homotopy theory in topolgy. A
    collapsible cell of the cyclic core allows the two recursive calls
    (cell-in and cell-out) to be encoded into one call. This reduces the
    number of recursive computations needed to solve the minimal covering
    problem. Connections to Unate Covering Problems(UCP), Binate Covering
    Problems (BCP), and MaxCostSAT are given.
  </abstract>

  <section|Introduction>

  Most work on minimal covering problems has focussed on operations involving
  the covering table. \ Essentiality, row dominance, column dominance and
  Gimpel's transform. \ Once \ a fixed-point of these operations is reached,
  the resulting sub problem, typically called the cyclic core, is solved by
  recursively by cho0sing a column to recurse on, using the branch and bound
  method.

  <new-line>The two-level logic exact minimization problem has a natural
  representation as an array of cubes of various dimensions. \ When looking
  at the resulting representation of a cyclic core, it was noticed that it
  was not truly cyclic in the algebraic topology sense, but had a number of
  free faces, which could be collapsed. \ \ By carrying along the face
  structure with the covering problem, we show that a free face does allow a
  reduction in the number of recursive calls to\ 

  \;

  <section|Definitions and Background>

  <subsection|Abstact Cell Complexes, Combinatorial Topology, and >

  Covering problems are typically solved using branch and bound algorithms,
  by realizing them in table form, followed by iterative reduction of the
  table by operations which leave the final\ 

  An abstract cell complex generalizes the representation of a structure in
  which to represent minimal covering problems, higher-order connectivity,
  cycles of any dimension, and geometric visualization of optimization
  problems.\ 

  <\definition>
    An <em|abstract cell complex> C = (S, Skel, <with|mode|math|\<leq\>,
    \ dim>\<leqslant\>\<leqslant\>) consists of:

    <\itemize>
      <item>A set S, a collection of subsets Skel, each of which is called a
      cell of C, and a partial order <with|mode|math|\<leq\>>, which captures
      the face relations of C.

      <item>A <em|<em|closure under intersection property><em|>> for Skel (if
      a, b <with|mode|math|\<epsilon\>> Skel, then a
      <with|mode|math|\<wedge\>>b <with|mode|math|\<varepsilon\>> Skel)

      <item>A <em|face closure property><strong|> for Skel (if a
      <with|mode|math|\<epsilon\>> Skel, and b <with|mode|math|\<leq\> a>
      then b <with|mode|math|\<varepsilon\>> Skel )

      <item>A dimension function (There is a function
      <with|mode|math|dim:Skel \<longrightarrow\> \<bbb-N\> such that dim(pt)
      = 0, and if \ b <with|mode|math|\<leq\> a>, then
      \ >dim(b)<with|mode|math|\<leq\>dim(a)>
    </itemize>
  </definition>

  <\definition>
    Let C be and abstract cell complex. Let c be a cell of C. \ c is said to
    be collapsible if c has a face f <with|mode|math|><with|mode|math|\<leq\>
    c>, such that dim(f) <with|mode|math|= dim(c) -1, \ >and f is not a face
    of q, for all q <with|mode|math|\<epsilon\>> C.
  </definition>

  From the area of topology called simple homotopy theory comes the concept
  of cellular collapses and expansions.\ 

  <\definition>
    \;

    If K and L are abstract cell complexes, we say that there is an
    elementary cell collapse from K to L (K<with|mode|math|\<searrow\>L>), if
    K = L <with|mode|math|\<cup\> e, where e is a cell of K>, with free face
    f not a face of any other face of L. \ Note: This is equivalent to the
    existence of a homotpy from K to L.

    <\definition>
      K is simple homotopy equivalent to L if there is a sequence of
      elematary collapses and expansions from K to L.
    </definition>
  </definition>

  <section|Minimization Process>

  An abstract cell complex can be used to represent a variety of problems.
  For example:

  <\enumerate-numeric>
    <item>Two-Level Boolean Logic Minimization, where each cell is an n-cube,
    and a collection of n-cubes represents the ON-set of a boolean function
    f.

    <item>Multi-Valued Logic Minimization, where each cell is an m<rsub|1> x
    m<rsub|2 >x ... x m<rsub|k> - hedron.

    <item>Deadlock complexes

    <item>Programs as fixed-points
  </enumerate-numeric>

  <subsection|Exact Two-Level Boolean Minimization>

  The object of this classical problem is given a boolean function f, find an
  exact \ minimum size representation of f as a sum-of-products cube
  representation of f. \ The usual algorithm is to

  <\enumerate-numeric>
    <item>Find all the prime implicants of f

    <item>Create the covering matrix of the primes of f, where the columns
    are the primes and the rows are the minterms of f.

    <item>Perform reductions on the covering matrix, until a fixed point
    table, called the cyclic-core \ is reached. The table reductions are:

    <\enumerate-roman>
      <item>Essentials reduction

      <item>Row dominance - a strongly equivalent operation

      <item>Column dominance - a weakly equivalent operation
    </enumerate-roman>

    <item>Recursively solve the cyclic-core problem by choosing a
    column(prime) to assume is first in the cover, find a recursive solution,
    and then is not in the cover, find a recursive solution to that problem,
    and then pick the cover that has the least number of elements as the
    minimal cover. \ Sophisticated branch and bound techniques, involving
    choosing a maximal independent set of elements at each cyclic-core
    recursion can be used to create a series of lower bounds on which to
    prune the recursions.
  </enumerate-numeric>

  <section|Description of Algorithm>

  <inactive|<inactive|Given the representation of a problem as an abstract
  cell complex C, let T<rsub|C> be the graded(by dimension)) covering table
  represented by a <with|mode|math|(<big|sum>>n<rsub|i>> x P) matrix of 0's
  and 1's, where P is the number of elements in the cover, and >n<rsub|i> is
  the number of elements of dimension i.

  \;

  The covering problem is to find a minimum set of columns of T<rsub|C> which
  cover C, and has minimal cost.

  \;

  The new contribution of this paper is two-fold: to introduce abstract cell
  complexes as a natural representation of combinatorial problems, and to
  show how this representation allows the introduction of a new reduction
  method during the cyclic-core recursive solution.

  \;

  <subsection|Collapsible Element Reduction>

  <\theorem>
    Given a \ collapsible element p in a graded covering matrix, which is a
    cyclic-core, remove the element p, and replace it with the set of free
    faces of p. \ Then one recursive call is all that is necessary to find
    the minimum cost cover of T<rsub|C>.

    \;

    <\proof>
      \ 
    </proof>

    This involves, at the covering matrix level, removing the \ column p, and
    replacing it with the set of one dimensional less columns which are the
    free faces of FreeFaces(p).

    \;

    Recursively continue to apply the non cyclic-core reductions, followed by
    the cyclic-core collapsible reduction, and return with a cover MinCov.
    \ Let \ FreeSize = <with|mode|math|<mid|\|>MinCov
    \<wedge\>FreeFaces(p)<mid|\|>>. \ If FreeSize
    <with|mode|math|\<geqslant\> 1 >, then put back in p to get the minimum
    cover. \ If FreeSize <with|mode|math|= 0 , > then MinCov is the minimum,
    as it's size will at most be one less than the minimum with the element p
    not included
  </theorem>

  \;

  <section|Acyclic Models>

  <section|Conclusions>

  <section|References>

  <new-page>

  \;
</body>

<\initial>
  <\collection>
    <associate|font-family|tt>
    <associate|language|verbatim>
    <associate|par-first|0cm>
  </collection>
</initial>

<\references>
  <\collection>
    <associate|auto-1|<tuple|1|?>>
    <associate|auto-10|<tuple|7|?>>
    <associate|auto-11|<tuple|8|?>>
    <associate|auto-12|<tuple|7|?>>
    <associate|auto-13|<tuple|8|?>>
    <associate|auto-14|<tuple|5.1|?>>
    <associate|auto-15|<tuple|6|?>>
    <associate|auto-16|<tuple|7|?>>
    <associate|auto-17|<tuple|8|?>>
    <associate|auto-2|<tuple|2|?>>
    <associate|auto-3|<tuple|2.1|?>>
    <associate|auto-4|<tuple|3|?>>
    <associate|auto-5|<tuple|3.1|?>>
    <associate|auto-6|<tuple|4|?>>
    <associate|auto-7|<tuple|4.1|?>>
    <associate|auto-8|<tuple|5|?>>
    <associate|auto-9|<tuple|6|?>>
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

      <with|par-left|<quote|1.5fn>|2.1<space|2spc>
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-3>>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|3<space|2spc>Abstract
      Cell Complex> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-4><vspace|0.5fn>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|4<space|2spc>Minimization
      Process> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-5><vspace|0.5fn>

      <with|par-left|<quote|1.5fn>|4.1<space|2spc>Exact Two-Level Boolean
      Minimization <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-6>>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|5<space|2spc>Description
      of Algorithm> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-7><vspace|0.5fn>

      <with|par-left|<quote|1.5fn>|5.1<space|2spc>Collapsible Element
      Reduction <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-8>>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|6<space|2spc>Acyclic
      Models> <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-9><vspace|0.5fn>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|7<space|2spc>Conclusions>
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-10><vspace|0.5fn>

      <vspace*|1fn><with|font-series|<quote|bold>|math-font-series|<quote|bold>|8<space|2spc>References>
      <datoms|<macro|x|<repeat|<arg|x>|<with|font-series|medium|<with|font-size|1|<space|0.2fn>.<space|0.2fn>>>>>|<htab|5mm>>
      <no-break><pageref|auto-11><vspace|0.5fn>
    </associate>
  </collection>
</auxiliary>
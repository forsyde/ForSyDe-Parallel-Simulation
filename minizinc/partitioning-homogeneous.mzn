include "globals.mzn";

%% parameters
int: M; % no. of available processors (maximum sub-simulation)
int: N; % number of processes

array[1..N] of int: e; % avg. exec. time of each process pi on the slowest processor
array[1..N,1..N] of int: c; % avg. comm. weight from pi to pj

% check for validity
constraint assert(M > 1,"Invalid datafile: " ++
	"Number of sub-simulations should be >0");

constraint assert(N > 1,"Invalid datafile: " ++
	"Number of processes should be >0");

% constraint variables
array[1..N] of var 1..M: m; % assignment of pi to a sub-network

%% constraints
% two redundant constrinats:
%constraint nvalue(n,m);
%constraint maximum(n, m);

% set constraint variables
% the partitions
array[1..M] of var set of 1..N: x;

% channeling constraints
% array[1..N,1..N] of var int: edges;
% constraint forall(i,j in 1..N) (edges[i,j]=(c[i,j]>0));
% constraint forall(i in 1..N, j in 1..M) (m[i]=j <-> i in x[j]);
constraint int_set_channel(m,x);

%constraint partition_set(x, 1..N);  %TODO: include or not to include?
int: avg = sum([e[i]|i in 1..N]) div M; % average execution time of all processes on fastest processors
%%%%
0..50: epsilon=50;
%%%%
% constraint forall (i in 1..M) ((sum (j in x[i]) (e[j])) *100 <= avg*(100+epsilon)) ;
array [1..M] of var int: diffs = [abs(sum (j in x[i]) (e[j]) - avg)|i in 1..M];
%var int: sumdiffs= sum(diffs);
var int: maxdiffs= max(diffs);
constraint maxdiffs * 100 <= avg * epsilon;

% Estimated execution time cost function for each process
var int : comm_cost;
constraint comm_cost =
    sum (i,j in 1..N) (
        bool2int(m[i]!=m[j])*c[i,j]
  );

% symmetry breaking: fix the smallest element in the partitions to be increasing
constraint forall (i in 2..M) ( min(x[i]) > min(x[i-1]) );


%% solving
solve :: seq_search([
%                 int_search([epsilon], input_order, indomain_random, complete),
                set_search(x, input_order, indomain_min, complete)    %TODO: which strategy?anti_first_fail?dom_w_deg?/indomain_interval?indomain_min?
%                 int_search(m, anti_first_fail, indomain_random, complete)
        ])
%       :: restart_luby(10)
      minimize (comm_cost);

%% printing human readable
%output ["mis={"]
%    ++ [show(m[i])++if i<N then "," else "" endif|i in 1..N]
%    ++ ["};\n"]
%    ++ ["partitions=" ++ show(x) ++ "};\n"]
%    ++ ["cost = " ++ show(comm_cost)]
%    ++ [" epsilon: " ++ show(epsilon/100)];
%% printing machine readable
output [show(m[i]-1)++"\n"|i in 1..N];

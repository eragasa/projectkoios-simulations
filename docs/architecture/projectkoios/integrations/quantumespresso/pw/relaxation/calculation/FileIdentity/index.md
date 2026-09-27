# `FileIdentity`

A file identity requires

$$
n>0,
\qquad
h=\operatorname{SHA256}(B),
$$

where `byte_size` is $n$ and `sha256` is the lowercase 64-digit digest $h$.
The immutable fields are `byte_size` and `sha256`.

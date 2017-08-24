//
//  bitfield.h
//
//  Created by Matthias Bartelmeß on 20.08.17.
//  Copyright © 2017 fourplusone. All rights reserved.
//

#ifndef bitfield_h
#define bitfield_h

#define BITFIELD_DECL(t, name, count) t name[(count/(sizeof(t)*8))+1]

#define bitfield_total_bits(bf) (sizeof(bf)*8)
#define bitfield_bits(bf) (sizeof(bf[0])*8)
#define bitfield_bit(bf, n) (n % bitfield_bits(bf))
#define bitfield_pos(bf, n) (n / bitfield_bits(bf))

#define bitfield_mask(bf) (1<<sizeof(bf[0]))
#define bitfield_protect(bf, n) (bitfield_total_bits(bf) > n)

#define bitfield_get(bf, n) ((bf[bitfield_pos(bf, n)] & (1 << bitfield_bit(bf, n) )) ? 1 : 0)
#define bitfield_set(bf, n) (n >= 0 ? (bf[bitfield_pos(bf, n)] |= 1 << bitfield_bit(bf, n)):0)
#define bitfield_unset(bf, n) (bf[bitfield_pos(bf, n)] ^=  (1 << bitfield_bit(bf, n)))
#define bitfield_set_value(bf, n, v) (v ? bitfield_set(bf, n) : bitfield_unset(bf, n))


#endif /* bitfield_h */

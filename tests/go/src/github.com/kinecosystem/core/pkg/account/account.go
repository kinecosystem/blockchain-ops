// Package account implements creating accounts and balance fetching logic.
package account

import (
	"math"

	"github.com/go-kit/kit/log"
	"github.com/go-kit/kit/log/level"
	"github.com/kinecosystem/go/build"
	"github.com/kinecosystem/go/keypair"

	"github.com/kinecosystem/core/pkg/errors"
	"github.com/kinecosystem/core/pkg/submit"
)

const maxOpsInTx = 100

type Keypair struct {
	Seed    string `json:"seed"`
	Address string `json:"address"`
}

type Keypairs struct {
	Keypairs []Keypair `json:"keypairs"`
}

func Create(horizonAddr string, network build.Network, funder *keypair.Full, accountsNum int, fundAmount string, logger log.Logger) ([]keypair.KP, error) {
	level.Info(logger).Log("msg", "creating accounts", "accounts_num", accountsNum)

	keypairs := make([]keypair.KP, 0, accountsNum)

	for batchIndex := 0; batchIndex <= (cap(keypairs)+1)/(maxOpsInTx+1); batchIndex++ {
		batch := keypairs[batchIndex*maxOpsInTx : int(math.Min(float64((batchIndex+1)*maxOpsInTx), float64(cap(keypairs))))]

		ops := make([]build.TransactionMutator, 0)
		for i := 0; i < len(batch); i++ {
			level.Info(logger).Log("msg", "adding create account operation", "account_index", batchIndex*maxOpsInTx+i)

			kp, err := keypair.Random()
			if err != nil {
				level.Error(logger).Log("msg", err, "account_index", batchIndex*maxOpsInTx+i, "seed", kp.Seed())
				return nil, err
			}
			keypairs = append(keypairs, kp)

			ops = append(ops, build.CreateAccount(
				build.Destination{AddressOrSeed: kp.Address()},
				build.NativeAmount{Amount: fundAmount}))
		}

		level.Info(logger).Log("msg", "submitting create account transaction")

		err := submit.SubmitWithRetry(horizonAddr, network, ops, funder.Seed(), logger)
		if err != nil {
			errors.GetTxErrorResultCodes(err, logger)
			return nil, err
		}

		for i, kp := range batch {
			level.Info(logger).Log(
				"msg", "new account created",
				"account_index", batchIndex*maxOpsInTx+i,
				"address", kp.Address(),
				"seed", kp.(*keypair.Full).Seed())
		}
	}

	return keypairs, nil
}

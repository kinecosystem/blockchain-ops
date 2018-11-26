package account

import (
	"github.com/go-kit/kit/log"
	"github.com/go-kit/kit/log/level"
	"github.com/stellar/go/clients/horizon"
	"github.com/stellar/go/keypair"
)

func logBalance(account *horizon.Account, logger log.Logger) {
	for _, balance := range account.Balances {
		level.Info(logger).Log("balance", balance.Balance, "asset_type", balance.Asset.Type)
	}
}

func logBalances(client horizon.ClientInterface, keypairs []keypair.KP, logger log.Logger) {
	for i, kp := range keypairs {
		l := log.With(logger, "account_index", i)

		if kp != nil {
			acc, err := client.LoadAccount(kp.Address())
			if err != nil {
				level.Error(l).Log("msg", err)
				continue
			}
			logBalance(&acc, l)
		}
	}
}
